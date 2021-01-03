# Changelog

<!-- skip title -->

## v0.6.5

*January 2, 2021*

* Happy New Year!
* Add support for `proxy_set_header` statements

## v0.6.4

*December 31, 2020*

* Add `force_exact` option to Certbot utilities

## v0.6.3

*December 30, 2020*

* Revise stop_service API

## v0.6.2

*December 30, 2020*

* Add ability to start and stop existing services
* Clean up API endpoints

## v0.6.1

*December 30, 2020*

* Fix bug that caused a server error when deleting a service

## v0.6.0

*December 28, 2020*

### NEW: Flask Integrations

* Add a Flask REST API, which can be optionally attached as a Blueprint
* Moved logs utility to a dedicated Flask utility framework, which can be optionally attached as a Blueprint

### Domain Management

* Add ability to *sign* wildcard certificates when adding domains to existing services
* Add ability to remove domains from existing services
* Modified `certbot` interfacing to call the command-line package instead of replicating its complicated inner workings

### Miscellaneous

* Instead of importing `sh` in `utils`, move the function to `utils`
* Replace all calls to `subprocess.run` with calls to `sh`
* Restructured documentation to collapse internal utilities

## v0.5.1

*December 23, 2020*

* Add logs index page to Flask integration

## v0.5.0

*December 22, 2020*

* Add ability to force `certbot` to use wildcard certificates (or bust)
* Modify README to use a PyPI badge instead of hardcoding the latest version

## v0.4.9

*December 21, 2020*

* Skip redundant deploy steps, such as when an nginx configuration already exists

## v0.4.8

*December 21, 2020*

* Concurrency: if `certbot` fails, wait 5 seconds and try again up to 5 times

## v0.4.7

*December 21, 2020*

* Provide a default value to `dna.utils.Logger.append`

## v0.4.6

*December 21, 2020*

* Add a flag to `dna.utils.Logger` to append instead of overwrite

## v0.4.5

*December 21, 2020*

* Add a flag to `dna.utils.sh` to return output instead of a generator
* Move socat binding to threads to speed up initialization

## v0.4.4

*December 21, 2020*

* Update module to include descriptions and links

## v0.4.3r1

*December 21, 2020*

* Bug fix: when using the fallback logger, *always* pass in the name of the requested, not only when the service isn't registered

## v0.4.3

*December 21, 2020*

* Add "Starting" and "Started" messages to DNA's internal logs

## v0.4.2

*December 21, 2020*

* Fix fallback logging passthrough (pass in the name of the requested service, instead of `None`)

## v0.4.1

*December 21, 2020*

* Initial release
