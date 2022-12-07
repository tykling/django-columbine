# django-columbine
A Django app which implements TDCs Columbine API.

## Installation
* Add "columbine" to settings.INSTALLED_APPS
* Migrate
* Run workers

## Theory of Operation
### Orders
All orders are contained in the Order model. To create a new order:

* Create a ShowNetInfo flow to find the circuits on the address
     * This will trigger creation of one or more ShowNetInfoVNAS flows
        * The result will be recorded as one or more instances of the VNAS model
* Create an Order object with an FK to the VNAS we want to use
    * This will trigger creation of an Order flow matching the technology for the chosen VNAS
        * The -validate transation reply will contain the products, productgroups, and product rules for that VNAS.
* In the Order object pick the products and how many we want, and supply any extra required parameters
* This means we can continue with the -order transaction of the Order flow

