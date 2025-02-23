# Analytics Recorder

Analytics Recorder is a client side library for our products to record data to [Labs Analytics Engine](https://github.com/pennlabs/labs-analytics). 

## Getting Started

### Global Singleton
To use the analytics recorder, you will need to create a singleton of the `AnalyticsRecorder` class. 

Create a file in your project's main directory and add call `get_analytics_recorder` with your product. 

e.g.
```
# pennmobile.analytics.py

from analytics.analytics import Product, get_analytics_recorder

LabsAnalytics = get_analytics_recorder(Product.MOBILE_BACKEND)
```

In prod, the actual recorder will be an instance of `LabsAnalyticsRecorder`. However when developing, this will fail on startup, and instead default to `LocalAnalyticsRecorder` which simply prints the data that would be sent to the console.

### Recording Events
Simply decorate the functions or views you want to record using a record function: 
- `record_apiview` for `APIViews` and `viewsets`
    
      @LabsAnalytics.record_apiview(
        ViewEntry(), # default logs 1 for every request
        ViewEntry(
            actions=["list"],
            name="long_results",
            filter_do_record=lambda _, res: len(res.data) > 9,
        ), # logs 1 if the response has more than 9 results
        ViewEntry(
            name="fail_message",
            only_on_failure=True,
            get_value=lambda _, res: res.data.get("error", "no error")
        ),
        ViewEntry(
            name="bookings_made",
            compute_before=lambda: GSRBooking.objects.count(),
            get_value_use_before=lambda _, __, before: GSRBooking.objects.count() - before
        ),
      )
      class MyViewSet(viewsets.ModelViewSet):
          ...

- `record_api_function` for functions inside of `views` (where the second argument is a `Request` object)

      @LabsAnalytics.record_api_function(
          FuncEntry(
              name="username_length",
              get_value=lambda args, _: len(args[1].user.username),
          ),
          FuncEntry(
              name="username_length2",
              get_value_with_args=lambda _self, req: len(req.user.username),
          ),
      )
      def get(self, request):
          ...
- `record_function`: for any other function
  
        @LabsAnalytics.record_function(
            get_username = lambda args, res: args[0].username
            FuncEntry(
                name="hours_used",
                get_value=lambda _args, hours: hours,
            ),
            FuncEntry(
                name="service",
                get_value_with_args=lambda _user, service: service
            ),
        )
        def compute_hours_used(user, service):
            ...
See documentation in source code for additional details about record functions and types of `AnalyticsEntry`s that can be used. 

## Our approach to Errors

Since we rely on the use of callbacks to control the data that is recorded, we introduce an additional place for errors. 

Our mental model here is that analytics is a crucial part of your routes and should be safe and free of bugs. Any unexpected errors in callbacks will throw a server 500 error just like as they would in a function. So developers should debug these with the same eagerness. 

Thus we do not provide the option to fail silently. 

The only place where we check for exceptions is in `filter_do_record` where we default to `False` if an exception is thrown.