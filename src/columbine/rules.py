import logging

from .models import (
    Order,
    OrderLine,
    RelationRule,
    RelationRuleType,
    ProductGroupCountRule,
    ProductCountRule,
    Product,
    ProductGroup,
)

logger = logging.getLogger("django_columbine.%s" % __name__)


class RuleChecker:
    """
    The Columbine RuleChecker class takes the order-validate TX with the Columbine products and "rules" as init
    arguments and can then be used to validate lists of tuples of product/count pairs which we intend to put in an order.
    """

    def __init__(self, tx):
        # make sure we have a clean ass to blow in
        OrderLine.objects.filter(order__flow=tx.flow).delete()
        Order.objects.filter(flow=tx.flow).delete()
        RelationRule.objects.filter(transaction=tx).delete()
        ProductGroupCountRule.objects.filter(productgroup__transaction=tx).delete()
        ProductCountRule.objects.filter(product__transaction=tx).delete()
        Product.objects.filter(transaction=tx).delete()
        ProductGroup.objects.filter(transaction=tx).delete()

        # save tx for later
        self.tx = tx

        # create product groups
        for productgroup in tx.reply_json["reply"]["product_group_list"][
            "product_group"
        ]:
            pg = ProductGroup.objects.create(
                transaction=tx,
                product_group_id=productgroup["product_group_id"],
                product_group_name=productgroup["product_group_name"],
                sik_value=productgroup["sik_value"],
            )
            logger.debug(
                "created %s with product_group_id %s sik_value %s and name %s"
                % (pg.tag, pg.product_group_id, pg.sik_value, pg.product_group_name)
            )

        # loop over and create products
        for product in tx.reply_json["reply"]["product_list"]["product"]:
            logger.debug(
                "creating product_id %s sik_value %s"
                % (product["product_id"], product["sik_value"])
            )
            p = Product.objects.create(
                transaction=tx,
                product_id=product["product_id"],
                name=product["name"],
                sik_value=product["sik_value"],
                descr=product["descr"],
                product_parameter_type_list=product["product_parameter_type_list"],
            )
            logger.debug(
                "created %s with product_id %s sik_value %s"
                % (p.tag, p.product_id, p.sik_value)
            )

            # loop over productgroups in json
            for pg in tx.reply_json["reply"]["product_group_list"]["product_group"]:
                # make sure we have a list
                products = self.force_list(pg["product_id_list"]["product_id"])

                # does this product belong in this group?
                if p.product_id in products and pg["sik_value"] == product["sik_value"]:
                    # add to group
                    ProductGroup.objects.get(
                        transaction=tx,
                        product_group_id=pg["product_group_id"],
                        product_group_name=pg["product_group_name"],
                        sik_value=pg["sik_value"],
                    ).products.add(p)
                    logger.debug("Added %s to group" % p)

        # get product count rules
        for rule in tx.reply_json["reply"]["product_count_rule_list"][
            "rule_product_count_product"
        ]:
            logger.debug("Saving rule %s" % rule)
            pcr = ProductCountRule.objects.create(
                product=Product.objects.get(
                    transaction=tx,
                    sik_value=rule["sik_value"],
                    product_id=rule["product_id"],
                ),
                min_value=rule["min_value"],
                max_value=rule["max_value"],
            )
            logger.info("Created %s" % pcr)

        logger.info("Getting productgroup count rules")
        for rule in tx.reply_json["reply"]["product_count_rule_list"][
            "rule_product_count_group"
        ]:
            logger.debug("saving rule %s" % rule)
            try:
                pg = ProductGroup.objects.get(
                    transaction=tx,
                    sik_value=rule["sik_value"],
                    product_group_id=rule["product_group_id"],
                )
            except ProductGroup.MultipleObjectsReturned:
                logger.exception(
                    "More than one ProductGroup returned, not sure where to put this rule :("
                )
                continue
            pgcr = ProductGroupCountRule.objects.create(
                productgroup=pg,
                min_value=rule["min_value"],
                max_value=rule["max_value"],
            )
            logger.info("Created %s" % pgcr)

        logger.info("Getting product relation rules...")
        for rule in tx.reply_json["reply"]["rule_relation_group_list"][
            "rule_relation_group"
        ]:
            print("working with rule:")
            print(rule)
            if not rule["rule_group_1"]["rule_product_unique_list"]:
                logger.error("No products in rule group 1, this rule is useless")
                continue

            if not rule["rule_group_2"]["rule_product_unique_list"]:
                logger.error("No products in rule group 2, this rule is useless")
                continue

            ruletype, created = RelationRuleType.objects.get_or_create(
                name=rule["rule_type"],
                descr=rule["descr"],
                defaults={"transaction": tx},
            )
            if created:
                logger.info("Created new RelationRuleType %s" % ruletype)
            rr = RelationRule.objects.create(transaction=tx, ruletype=ruletype)

            # add product from group 1
            for product in self.force_list(
                rule["rule_group_1"]["rule_product_unique_list"]["product_unique"]
            ):
                print("adding product %s to group 1" % product)
                rr.rule_group_1_products.add(
                    Product.objects.get(
                        product_id=product["product_id"], sik_value=product["sik_value"]
                    )
                )

            # add product from group 2
            for product in self.force_list(
                rule["rule_group_2"]["rule_product_unique_list"]["product_unique"]
            ):
                print("adding product %s to group 2" % product)
                rr.rule_group_2_products.add(
                    Product.objects.get(
                        product_id=product["product_id"], sik_value=product["sik_value"]
                    )
                )

            logger.debug(
                "%s now has %s products in rule_group_1 and %s products in rule_group_2"
                % (
                    rr,
                    rr.rule_group_1_products.count(),
                    rr.rule_group_2_products.count(),
                )
            )
            if rr.rule_group_1_products.count() == 0:
                logger.warning("%s HAS 0 PRODUCTS IN GROUP 1" % rr)
            if rr.rule_group_2_products.count() == 0:
                logger.warning("%s HAS 0 PRODUCTS IN GROUP 2" % rr)

        logger.info("Done initialising RuleChecker!")

    def force_list(self, data):
        """
        Takes some input, wraps it in a [list] unless it already is a list
        """
        if isinstance(data, (str, dict)):
            return [data]
        elif isinstance(data, list):
            return data
        else:
            logger.error(
                "what to do? input is of type %s and is %s" % (type(data), data)
            )
            return False

    def validate(self):
        """
        Get the Order object and validate the products in it
        """
        order = self.tx.flow.orders.get()
        logger.info("going to validate products in order %s" % order)

        for orderline in order.orderlines.all():
            if orderline.product.product_count_rules.exists():
                logger.info("checking product count rules for %s" % orderline)
            else:
                logger.warning("No ProductCountRule found for %s" % orderline)
                continue

            # is the count below the limit?
            if orderline.count < orderline.product.product_count_rules.get().min_value:
                logger.error(
                    "Product count for this product is lower than the minimum value defined by rule %s: %s"
                    % (orderline.product, orderline.product.product_count_rules.get())
                )
                return False

            # is the count above the limit?
            if orderline.count > orderline.product.product_count_rules.get().max_value:
                logger.error(
                    "Product count for this product is higher than the maximum value defined by rule %s: %s"
                    % (orderline.product, orderline.product.product_count_rules.get())
                )
                return False

            logger.info(
                "No problem found for product %s rule %s"
                % (orderline.product, orderline.product.product_count_rules.get())
            )

        logger.warning(
            "NOT CHECKING PRODUCT GROUP COUNT RULES SINCE THEY MAKE NO SENSE AND WE DONT KNOW HOW THEY WORK :("
        )

        logger.info("Looping over relationrules....")
        for rule in self.tx.relationrules.all():
            logger.debug(
                "checking rule %s - type %s - %s"
                % (rule, rule.ruletype, rule.ruletype.name)
            )

            if rule.ruletype.name == "combination-not-allowed":
                # If one or more products in rule-group-1 are selected,
                # it is not allowed to select one or more products in rule-group-2
                if order.orderlines.filter(
                    product__in=rule.rule_group_1_products
                ).exists():
                    if order.orderlines.filter(
                        product__in=rule.rule_group_2_products
                    ).exists():
                        logger.error("Failed on %s" % rule)
                        return False
            elif rule.ruletype.name == "conditional-select":
                # If one or more products in rule-group-1 are selected,
                # one or more products in rule-group-2 must be selected
                if order.orderlines.filter(
                    product__in=rule.rule_group_1_products
                ).exists():
                    if not order.orderlines.filter(
                        product__in=rule.rule_group_2_products
                    ).exists():
                        logger.error("Failed on %s" % rule)
                        return False
            elif rule.ruletype.name == "conditional-select-all":
                # If one or more products in rule-group-1 are selected,
                # all products in rule-group-2 must be selected
                if order.orderlines.filter(
                    product__in=rule.rule_group_1_products
                ).exists():
                    if rule.rule_group_2_products.exclude(
                        product__in=order.products.all()
                    ).exists():
                        logger.error("Failed on %s" % rule)
                        return False
            elif rule.ruletype.name == "conditional-select-all-all":
                # If all products in rule-group-1 are selected,
                # all products in rule-group-2 must be selected
                if not rule.rule_group_1_products.exclude(
                    product__in=order.products.all()
                ).exists():
                    if rule.rule_group_2_products.exclude(
                        product__in=order.products.all()
                    ).exists():
                        logger.error("Failed on %s" % rule)
                        return False
            elif rule.ruletype.name == "conditional-select-one":
                # If one or more products in rule-group-1 are selected,
                # exactly one product in rule-group-2 must be selected
                if order.orderlines.filter(
                    product__in=rule.rule_group_1_products
                ).exists():
                    if (
                        order.orderlines.filter(
                            product__in=rule.rule_group_2_products
                        ).count()
                        != 1
                    ):
                        logger.error("Failed on %s" % rule)
                        return False
            elif rule.ruletype.name == "parameter-value-not-allowed":
                # If one or more products in rule-group-1 are selected,
                # parameter values must not be specified for products in rule-group-2
                if order.orderlines.filter(
                    product__in=rule.rule_group_1_products
                ).exists():
                    if order.orderlines.filter(
                        product__in=rule.rule_group_2_products,
                        product_parameter_type_list__isnull=True,
                    ).exists():
                        logger.error("Failed on %s" % rule)
                        return False
            elif rule.ruletype.name == "parameter-value-required":
                # the behaviour of this rule depends on the rule_group_3_products field
                if rule.rule_group_3_products.exists():
                    # If one or more products in rule-group-1 are selected and one or more in rule-group-2,
                    # parameter values must be specified for products in rule-group-3
                    if (
                        order.orderlines.filter(
                            product__in=rule.rule_group_1_products
                        ).exists()
                        and order.orderlines.filter(
                            product__in=rule.rule_group_2_products
                        ).exists()
                    ):
                        if order.orderlines.filter(
                            product__in=rule.rule_group_3_products,
                            product_parameter_type_list__isnull=True,
                        ).exists():
                            logger.error("Failed on %s" % rule)
                            return False
                else:
                    # If one or more products in rule-group-1 are selected,
                    # parameter values must be specified for products in rule-group-2
                    if order.orderlines.filter(
                        product__in=rule.rule_group_1_products
                    ).exists():
                        if order.orderlines.filter(
                            product__in=rule.rule_group_2_products,
                            product_parameter_type_list__isnull=False,
                        ).exists():
                            logger.error("Failed on %s" % rule)
                            return False
            elif rule.ruletype.name == "parameter-value-uppercase":
                # Specified parameter values for products in rule-group-1 must be in UPPERCASE
                # TODO: implement this when we know what the data looks like
                pass
            elif rule.ruletype.name == "select":
                # One or more products in rule-group-1 must be selected
                if not order.orderlines.filter(
                    product__in=rule.rule_group_1_products
                ).exists():
                    logger.error("Failed on %s" % rule)
                    return False
            elif rule.ruletype.name == "select-all":
                # All products in rule-group-1 must be selected
                if not rule.rule_group_1_products.exclude(
                    product__in=order.products.all()
                ).exists():
                    logger.error("Failed on %s" % rule)
                    return False
            elif rule.ruletype.name == "select-one":
                # Exactly one product in rule-group-1 must be selected
                if (
                    not order.orderlines.filter(
                        product__in=rule.rule_group_1_products
                    ).count()
                    == 1
                ):
                    logger.error("Failed on %s" % rule)
                    return False
            elif rule.ruletype.name == "select-when-no-parameter":
                # If parameter values are Not specified for products in rule-group-1,
                # one or more products in rule-group-2 must be selected
                if order.orderlines.filter(
                    product__in=rule.rule_group_1_products,
                    product_parameter_type_list__isnull=True,
                ).exists():
                    if not order.orderlines.filter(
                        product__in=rule.rule_group_2_products
                    ).exists():
                        logger.error("Failed on %s" % rule)
                        return False
            elif rule.ruletype.name == "select-when-parameter":
                # If parameter values are specified for products in rule-group-1,
                # one or more products in rule-group-2 must be selected
                if order.orderlines.filter(
                    product__in=rule.rule_group_1_products,
                    product_parameter_type_list__isnull=False,
                ).exists():
                    if not order.orderline.filter(
                        product__in=rule.rule_group_2_products
                    ).exists():
                        logger.error("Failed on %s" % rule)
                        return False
            elif rule.ruletype.name == "supply-parameter-value":
                # If parameter values are specified for products in rule-group-1,
                # parameter values must be specified for products in rule-group-2
                if order.orderlines.filter(
                    product__in=rule.rule_group_1_products,
                    product_parameter_type_list__isnull=False,
                ).exists():
                    if not order.orderline.filter(
                        product__in=rule.rule_group_2_products,
                        product_parameter_type_list__isnull=True,
                    ).exists():
                        logger.error("Failed on %s" % rule)
                        return False
            elif rule.ruletype.name == "supply-parameter-value-all":
                # If parameter values are specified for one or more products in rule-group-1,
                # parameter values must be specified for all products in rule-group-1
                if order.orderlines.filter(
                    product__in=rule.rule_group_1_products,
                    product_parameter_type_list__isnull=False,
                ).exists():
                    if order.orderlines.filter(
                        product__in=rule.rule_group_1_products,
                        product_parameter_type_list__isnull=True,
                    ).exists():
                        logger.error("Failed on %s" % rule)
                        return False
            else:
                raise NotImplementedError("Unknown ruletype %s" % rule.ruletype.name)

        logger.info("Done checking relationrules....")
