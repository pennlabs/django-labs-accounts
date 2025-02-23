from abc import ABC
from dataclasses import dataclass
from datetime import timedelta
from string import Template
from typing import Any, Callable, List, Optional, TypeVar, Unpack

from django.utils import timezone


BeforeContext = TypeVar("BeforeContext")
FunctionParam = TypeVar("FunctionParam")
FunctionReturn = TypeVar("FunctionReturn")


@dataclass
class AnalyticsEntry(ABC):
    """
    Dataclass to represent an analytics entry to be recorded

    name: name to be included in the generated key
    value: value to be recorded
    get_value: function to get the value to be recorded
    get_value_use_before: function to get the value to be recorded using the before context
    compute_before: function to compute some context before the view/function is called
    filter_do_record: function to determine if the entry should be recorded,
                        defaults to not record if exception is thrown

    * Only one type of value "getter" should be supplied.
    """

    name: Optional[str] = None
    value: Optional[Any] = None
    get_value: Optional[Callable[[FunctionParam, FunctionReturn], Any]] = None
    get_value_use_before: Optional[
        Callable[[FunctionParam, FunctionReturn, BeforeContext], Any]
    ] = None
    compute_before: Optional[Callable[[], BeforeContext]] = None
    filter_do_record: Optional[Callable[[FunctionParam, FunctionReturn], bool]] = None

    def __post_init__(self):
        values_supplied = len(
            [
                v
                for v in [self.value, self.get_value, self.get_value_use_before]
                if v is not None
            ]
        )
        if values_supplied > 1:
            raise ValueError(
                "Cannot specify more than one of value, get_value, and get_value_use_before"
            )
        if values_supplied > 0 and self.name is None:
            raise ValueError(
                "Must specify name if value, get_value, or get_value_use_before is specified"
            )

    def _compute_value(self, func_param, func_return, before_context) -> str:
        if self.value is not None:
            ret = self.value
        elif self.get_value is not None:
            ret = self.get_value(func_param, func_return)
        elif self.get_value_use_before is not None:
            ret = self.get_value_use_before(func_param, func_return, before_context)
        else:
            ret = 1
        return str(ret)

    def _compute_filter_do_record(self, func_param, func_return) -> bool:
        if self.filter_do_record:
            try:
                return self.filter_do_record(func_param, func_return)
            except Exception:
                return False
        return True

    def _compute_data(
        self, key_template, func_param, func_return, before_context
    ) -> Optional[dict]:
        if self._compute_filter_do_record(func_param, func_return):
            return {
                "key": key_template.substitute(
                    name=f".{self.name}" if self.name else ""
                ),
                "value": self._compute_value(func_param, func_return, before_context),
            }

    @staticmethod
    def compute_before_contexts(entries) -> List[Optional[BeforeContext]]:
        return [e.compute_before and e.compute_before() for e in entries]

    @staticmethod
    def compute_data_list(
        key_template: Template,
        func_param: FunctionParam,
        func_return: FunctionReturn,
        entries: List["AnalyticsEntry"],
        before_contexts: List[Optional[BeforeContext]],
    ):
        return [
            data
            for e, before_context in zip(entries, before_contexts)
            if (
                data := e._compute_data(
                    key_template, func_param, func_return, before_context
                )
            )
        ]


@dataclass
class ViewEntry(AnalyticsEntry):
    """
    Entry to be used with a Django View

    The type FunctionParam (e.g. for get_value) will be the Request object
    The type FunctionReturn (e.g. for get_value) will be the Response object

    actions: list of actions to record if using a ViewSet (default is all)
    methods: list of methods to record if using a APIView (default is all)
    """

    actions: Optional[List[str]] = None
    methods: Optional[List[str]] = None
    filter_do_record = lambda self, _, res: res.status_code < 400  # noqa: E731

    def __post_init__(self):
        super().__post_init__()
        if self.actions is not None and self.methods is not None:
            raise ValueError("Cannot specify both actions and methods")

    def accept_action(self, action):
        if self.actions is None:
            return True
        return action in self.actions

    def accept_method(self, method):
        return self.methods is None or method in self.methods


@dataclass
class FuncEntry(AnalyticsEntry):
    """
    Entry to be used with a function

    The type FunctionParam (e.g. for get_value) will be a tuple of all explicitly defined arguments
    (everything before *args or **kwargs) as defined on the decorated function itself. The tuple
    will NOT be based off of how a caller may call the function
    The type FunctionReturn (e.g. for get_value) will be the return value of the decorated function

    get_value_with_args: function to get the value to be recorded but takes in the positional
    arguments unpacked as arguments

    * Only one type of value "getter" should be supplied.
    """

    get_value_with_args: Optional[Callable[[Unpack[FunctionParam]], Any]] = None

    def __post_init__(self):
        values_supplied = len(
            [
                v
                for v in [
                    self.value,
                    self.get_value,
                    self.get_value_use_before,
                    self.get_value_with_args,
                ]
                if v is not None
            ]
        )
        if values_supplied > 1:
            raise ValueError(
                "Cannot specify more than one of "
                "value, get_value, get_value_use_before, and get_value_with_args"
            )
        if values_supplied > 0 and self.name is None:
            raise ValueError(
                "Must specify name if "
                "value, get_value, get_value_use_before, or get_value_with_args is specified"
            )
        return super().__post_init__()

    def _compute_value(self, func_param, func_return, before_context):
        if self.get_value_with_args is not None:
            return self.get_value_with_args(*func_param)
        return super()._compute_value(func_param, func_return, before_context)


class UnaryFuncEntry(AnalyticsEntry):
    """
    Like FuncEntry but simpler for functions with only one argument

    The type FunctionParam (e.g. for get_value) will be the single argument as defined on the
    decorated function itself.
    The type FunctionReturn (e.g. for get_value) will be the return value of the decorated function.
    """

    pass


# class _GenericEntry(ViewEntry, FuncEntry, UnaryFuncEntry):
#     """
#     Generic entry that can be used for any type of function or view. This is
#     not really safe since it relies on the underlying classes to not have any
#     overlapping fields being overriden, so users should not create this directly as to
#     not have dependencies on this code.

#     NOTE:
#     The "correct" way to create library defined entries may just be to create one
#     for each type of AnalyticsEntry we want to support that the entry should be for.

#     For now we use this for simplicity, thus new entry classes should be included as a class
#     this derives from. But, careful thought should be given if the design of entry classes
#     changes too much as to whether _GenericEntry is still appropriate.
#     """

#     pass


def to_microsecond(delta):
    return int(delta / timedelta(microseconds=1))


ViewEntry.time = ViewEntry(
    name="time",
    compute_before=lambda: timezone.now(),
    get_value_use_before=lambda _, __, start_time: to_microsecond(
        timezone.now() - start_time
    ),
)

ViewEntry.status = ViewEntry(
    name="status", get_value=lambda _, res: res.status_code, filter_do_record=None
)

ViewEntry.failure_status = ViewEntry(
    name="failure_status",
    get_value=lambda _, res: res.status_code,
    filter_do_record=lambda _, res: res.status_code >= 400,
)

FuncEntry.time = FuncEntry(
    name="time",
    compute_before=lambda: timezone.now(),
    get_value_use_before=lambda _, __, start_time: to_microsecond(
        timezone.now() - start_time
    ),
)

FuncEntry.status = FuncEntry(
    name="status",
    get_value=lambda _, res: res.status_code,
)

FuncEntry.failure_status = FuncEntry(
    name="failure_status",
    get_value=lambda _, res: res.status_code,
    filter_do_record=lambda _, res: res.status_code >= 400,
)


__all__ = ["ViewEntry", "FuncEntry", "UnaryFuncEntry"]
