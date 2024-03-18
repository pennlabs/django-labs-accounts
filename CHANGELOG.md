Changelog
=========

x.y.z (UNRELEASED)
------------------
* Changes

0.9.5 (2024-03-02)
------------------
* Mandate Python 3.11 and Django 5.0.2

0.9.4 (2023-08-27)
------------------
* Authenticate user in TokenView for mobile users

0.9.3 (2023-08-25)
------------------
* Fix login regression for new mobile users

0.9.0 (2023-02-05)
------------------
* Introduced B2B IPC

0.8.0 (2021-08-28)
------------------
* Switch IPC on behalf of the user receiving end to use a django rest framework authentication class

0.7.1 (2021-01-03)
------------------
* Scope platform groups to be able to properly update group information

0.7.0 (2020-07-28)
------------------
* Add sentry logging
* Add failback default with next parameters

0.6.1 (2020-02-21)
------------------
* Refactor user permissions with updated Platform
* Add group syncing

0.6.0 (2020-02-11)
------------------
* Restrict redirects to be relative

0.5.4 (2020-01-20)
------------------
* Create a user if one doesn't exist when receiving an IPC call

0.5.3 (2020-01-13)
------------------
* Auto generate REDIRECT_URI if not provided

0.5.2 (2019-12-22)
------------------
* Test release (no changes from 0.5.1)

0.5.1 (2019-12-20)
------------------
* Fix: requests typo

0.5.0 (2019-12-09)
------------------
* Feature: IPC receiving middleware
* Feature: IPC sending helper method
* Feature: Better documentation
* Fix: Better error checking

0.4.2 (2019-11-14)
------------------
* Fix: Register models from the default django admin

0.4.1 (2019-11-10)
------------------
* Feature: Update admin permissions on each login

0.4.0 (2019-11-08)
------------------
* Feature: Transition to PennIDs for authentication
* Feature: Add additional method to run after user authentication

0.3.8 (2019-10-20)
------------------
* Fix: Use POST in introspect call

0.3.7 (2019-09-07)
------------------
* Feature: Custom admin login handler

0.3.6 (2019-08-18)
------------------
* Feature: Allow redirect to be specified on logout

0.3.5 (2019-08-18)
------------------
* Fix: Callback when multiple redirect_uris are defined

0.3.4 (2019-08-12)
------------------
* Feature: Add logout route

0.3.3 (2019-08-12)
------------------
* Fix: Callback token request
* Fix: Installation documentation

0.3.2 (2019-04-23)
------------------
* Fix: Corrupt pypi release

0.3.1 (2019-04-23)
------------------
* Fix: Remove unneeded migrations files

0.3.0 (2019-04-23)
------------------
* Fix: Remove custom user model and rely on default django model
* Fix: Update authentication backend to fit platform

0.2.0 (2019-03-24)
------------------
* New feature: Provide an easier way to access settings through a new `accounts_settings` object

0.1.0 (2019-03-17)
------------------
* Initial Release
