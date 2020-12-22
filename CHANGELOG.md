# Changelog

<!-- skip title -->

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