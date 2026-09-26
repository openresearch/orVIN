# Validation database license

Contains information from Washington State Department of Licensing's [Electric Vehicle Population Data](https://data.wa.gov/Transportation/Electric-Vehicle-Population-Data/f6w7-q2d2), available under the [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/).

The grouped source database in `groups.json.gz` and derived prefix-result databases in this directory are made available under ODbL 1.0. Retain this notice and the attribution in `source.json`. See the linked license for the complete terms, including attribution, redistribution and derivative-database share-alike requirements. This directory's database license is separate from the repository's software license.

Modifications: records grouped by the published first ten VIN characters, make, model and model year, with registration counts aggregated. No owner or location data retained. Derived results add consensus predictions from declared synthetic continuations; they do not identify actual complete vehicles or factories.
