# Changelog

<!-- skip title -->

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