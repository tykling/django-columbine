import logging

from django.contrib import admin
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe
from django.shortcuts import reverse

from .models import (
    Flow,
    Transaction,
    Request,
    VNAS,
    Event,
    Order,
    RelationRule,
    RelationRuleType,
    ProductCountRule,
    Product,
    ProductGroup,
)


logger = logging.getLogger("django_columbine.%s" % __name__)


def get_product_name(rule):
    return rule.product.name


get_product_name.short_description = "Product Name"


def get_transaction(obj, transaction_field="transaction"):
    """
    Return a HTML link to the flow
    """
    return mark_safe(
        "<a href='%s'>%s</a>"
        % (
            reverse(
                "admin:columbine_transaction_change",
                kwargs={"object_id": getattr(obj, transaction_field).uuid},
            ),
            obj.flow.tag,
        )
    )


get_transaction.short_description = "Transaction"


def get_flow(obj, flow_field="flow"):
    """
    Return a HTML link to the flow
    """
    return mark_safe(
        "<a href='%s'>%s</a>"
        % (
            reverse(
                "admin:columbine_flow_change",
                kwargs={"object_id": getattr(obj, flow_field).uuid},
            ),
            obj.flow.tag,
        )
    )


get_flow.short_description = "Flow"


def get_vnas(obj, vnas_field="vnas"):
    """
    Return a HTML link to the VNAS
    """
    return mark_safe(
        "<a href='%s'>%s</a>"
        % (
            reverse(
                "admin:columbine_vnas_change",
                kwargs={"object_id": getattr(obj, vnas_field).uuid},
            ),
            obj.vnas.tag,
        )
    )


get_vnas.short_description = "VNAS"


def get_product_count(productgroup):
    """
    Return the number of products in the productgroup
    """
    return productgroup.products.count()


get_product_count.short_description = "Product Count"


def get_products(obj, m2m_field="products"):
    """
    Return a HTML list of links to the products in the m2m field
    """
    return format_html_join(
        mark_safe("<br>"),
        '<a href="{}">{} ({})</a>',
        [
            (
                reverse(
                    "admin:columbine_product_change", kwargs={"object_id": product.uuid}
                ),
                product.name or "NONAME",
                product.product_id,
            )
            for product in getattr(obj, m2m_field).all()
        ],
    ) or mark_safe("<span class='errors'>No products found</span>")


get_products.short_description = "Products"


def get_rulegroup_1_products(obj):
    """ Return all products from rule_group_1 """
    return get_products(obj, m2m_field="rule_group_1_products")


get_rulegroup_1_products.short_description = "Rule Group 1 Products"


def get_rulegroup_2_products(obj):
    """ Return all products from rule_group_2 """
    return get_products(obj, m2m_field="rule_group_2_products")


get_rulegroup_2_products.short_description = "Rule Group 2 Products"


def get_rulegroup_3_products(obj):
    """ Return all products from rule_group_3 """
    return get_products(obj, m2m_field="rule_group_3_products")


get_rulegroup_3_products.short_description = "Rule Group 3 Products"


def get_ruletype(obj):
    """ Return a HTML link to the relation rule type """
    return mark_safe(
        "<a href='%s'>%s</a><br>%s"
        % (
            reverse(
                "admin:columbine_relationruletype_change",
                kwargs={"object_id": obj.ruletype.uuid},
            ),
            obj.ruletype.name,
            obj.ruletype.descr,
        )
    )


get_ruletype.short_description = "Relation Rule Type"


def get_groups(product, fieldname="productgroup_set"):
    """
    Return a HTML list of links to the product groups
    """
    return format_html_join(
        mark_safe("<br>"),
        '<a href="{}">{}</a>',
        [
            (
                reverse(
                    "admin:columbine_productgroup_change", kwargs={"object_id": pg.id}
                ),
                pg.name,
            )
            for pg in getattr(product, fieldname).all()
        ],
    ) or mark_safe("<span class='errors'>No productgroups found</span>")


get_groups.short_description = "Product Groups"


class TransactionInline(admin.TabularInline):
    model = Transaction


class RequestInline(admin.TabularInline):
    model = Request


class ProductGroupInline(admin.TabularInline):
    model = ProductGroup.products.through


class OrderValidateTransactionListFilter(admin.SimpleListFilter):
    """
    A custom SimpleListFilter to show only the relevant Transactions in the sidebar
    """

    title = "Transaction"
    parameter_name = "transaction"

    def lookups(self, request, model_admin):
        """
        Return a list of tuples with the uuids of the
        Transactions with stage validate and which belong
        to one of the *OrderFlow flows.
        """
        return [
            (tx.uuid, tx.uuid)
            for tx in Transaction.objects.filter(
                stage="validate", flow__name__endswith="OrderFlow"
            )
        ]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value():
            return queryset.filter(transaction_id=self.value())
        return queryset


# ModelAdmin classes below here #


@admin.register(Flow)
class FlowAdmin(admin.ModelAdmin):
    def get_tag(self, obj):
        return obj.tag

    list_display = [
        "get_tag",
        "name",
        "kwargs",
        "created_date",
        "modified_date",
        "columbine_session_id",
        "finished",
        "error",
    ]

    list_filter = ["name", "finished"]

    inlines = [TransactionInline]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    def get_tag(self, obj):
        return obj.tag

    list_display = [
        "get_tag",
        "flow",
        "stage",
        "request_json",
        "request_xml_valid",
        "reply_json",
        "reply_xml_valid",
        "result",
        "error",
    ]

    list_filter = ["stage", "result"]

    inlines = [RequestInline]


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ["transaction", "request_headers", "response_headers"]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        "transaction",
        "name",
        "event_id",
        "phone_number",
        "event_time",
        "order_number",
        "order_status",
    ]


@admin.register(VNAS)
class VNASAdmin(admin.ModelAdmin):
    list_display = ["uuid", get_flow, "references"]


@admin.register(ProductGroup)
class ProductGroupAdmin(admin.ModelAdmin):
    list_display = [
        "uuid",
        get_flow,
        "product_group_id",
        "product_group_name",
        "sik_value",
        get_product_count,
        get_products,
    ]

    get_products.short_description = "Products"

    list_filter = [
        "product_group_id",
        "product_group_name",
        "sik_value",
        OrderValidateTransactionListFilter,
    ]

    inlines = [ProductGroupInline]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "product_id",
        "name",
        "sik_value",
        "product_parameter_type_list",
        get_groups,
    ]

    inlines = [ProductGroupInline]

    search_fields = ["uuid", "product_id", "name"]


@admin.register(ProductCountRule)
class ProductCountRuleAdmin(admin.ModelAdmin):
    list_display = ["product", get_product_name, "min_value", "max_value"]
    list_filter = ["min_value", "max_value", "product"]


@admin.register(RelationRuleType)
class RelationRuleTypeAdmin(admin.ModelAdmin):
    list_display = [get_flow, "name", "descr"]
    list_filter = ["name", OrderValidateTransactionListFilter]


@admin.register(RelationRule)
class RelationRuleAdmin(admin.ModelAdmin):
    list_display = [
        "uuid",
        get_flow,
        get_ruletype,
        get_rulegroup_1_products,
        get_rulegroup_2_products,
    ]

    list_filter = ["ruletype", OrderValidateTransactionListFilter]


class OrderLineInline(admin.TabularInline):
    model = Order.products.through


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["uuid", get_vnas, get_products, "references"]

    inlines = [OrderLineInline]

    search_fields = ["flow", "products"]
