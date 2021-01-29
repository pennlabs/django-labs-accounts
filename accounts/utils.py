from accounts.ipc import authenticated_request
from accounts.settings import accounts_settings


def getFullUser(user):
    # hopefully works, might need to manually get phone numbers and emails
    return authenticated_request(user, "POST", accounts_settings.PLATFORM_URL + "/accounts/me/")


def updateUser(user, user_params):
    # do we want to validate the params before, or trust the product?
    return authenticated_request(user, "PATCH", accounts_settings.PLATFORM_URL + "/accounts/me/", "user_params")
