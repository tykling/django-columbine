import logging


logger = logging.getLogger("django_columbine.%s" % __name__)


class ColumbineClient:
    """
    Base class used by all the Client classes
    """

    def __init__(self, reason, source, references, parent_flow=None):
        """
        Save data for use later, TODO: switch to use @dataclass operator
        """
        self.reason = reason
        self.source = source
        self.references = references
        self.parent_flow = parent_flow


class ShowNetInfoClient(ColumbineClient):
    """
    This class contains the methods used to create show-net-info Flow
    objects. This API call has three different lookup modes:

    1) Search for a circuit number/phone number. If the circuit
    number/phone number is not "ours" this must also include zip-code
    and house-no. TODO: This has not been implemented yet.

    2) Search for installation address. The address must be unique in
    columbine or an error will be returned.

    Both 1 and 2 return a list of 1-n "visitationNodeAnalysisSeq" IDs for
    use in 3).

    3) Direct search for an address and a specific
    "visitationNodeAnalysisSeq" ID. This returns the full actual
    information we want.

    A typical lookup will consist of two flows, 1) or 2) to find the
    relevant "visitationNodeAnalysisSeq" ID(s), and then one or more
    of 3) to get the data for them.
    """

    def visitation_node_analysis_seq(
        self, vnas, street_name, house_no, zip_code, city=None, floor=None, door_no=None
    ):
        """
        Create Flow to search for a specific visitationNodeAnalysisSeq at an address
        """
        # prepare kwargs
        kwargs = {
            "visitationNodeAnalysisSeq": vnas,
            "street-name": street_name,
            "house-no": house_no,
            "zip-code": zip_code,
        }
        if city:
            kwargs["city"] = city
        if floor:
            kwargs["floor"] = floor
        if door_no:
            kwargs["door-no"] = door_no

        # create the flow
        from columbine.models import Flow

        flow = Flow.objects.create(
            name="ShowNetInfoVNASFlow",
            reason=self.reason,
            source=self.source,
            references=self.references,
            parent_flow=self.parent_flow,
            kwargs=kwargs,
        )

        logger.info("Created new ShowNetInfoVNASFlow %s" % flow)
        return flow

    def address(
        self, street_name, house_no, zip_code, city=None, floor=None, door_no=None
    ):
        """
        Create flow to call the ShowNetInfo service with an address.
        """
        # prepare kwargs
        kwargs = {
            "street-name": street_name,
            "house-no": house_no,
            "zip-code": zip_code,
        }
        if floor:
            kwargs["floor"] = floor
        if door_no:
            kwargs["door-no"] = door_no

        # create the flow
        from columbine.models import Flow

        flow = Flow.objects.create(
            name="ShowNetInfoAddressFlow",
            reason=self.reason,
            source=self.source,
            references=self.references,
            parent_flow=self.parent_flow,
            kwargs=kwargs,
        )
        logger.info("Created new ShowNetInfoAddressFlow %s" % flow)
        return flow

    def lid(self, phone_no, zip_code=None, house_no=None):
        """
        Create flow to search the ShowNetInfo service with a lid
        (lednings id, which is a phonenumber or circuitnumber).
        """
        # prepare kwargs
        kwargs = {"phone-no": house_no}
        if zip_code:
            kwargs["zip-code"] = zip_code
        if house_no:
            kwargs["house-no"] = house_no

        # create the flow
        from columbine.models import Flow

        flow = Flow.objects.create(
            name="ShowNetInfoFlow",
            reason=self.reason,
            source=self.source,
            references=self.references,
            parent_flow=self.parent_flow,
            kwargs=kwargs,
        )

        logger.info("Created new ShowNetInfoLIDFlow %s" % flow)
        return flow


class GetEventStatusClient(ColumbineClient):
    """
    A simple client to create a GetEventStatus flow
    """

    def get_event_status(self):
        from columbine.models import Flow

        flow = Flow.objects.create(
            name="GetEventStatusFlow",
            parent_flow=self.parent_flow,
            reason=self.reason,
            source=self.source,
            references=self.references,
        )
        logger.info("Created new GetEventStatusFlow %s" % flow)
        return flow


class GetEventsClient(ColumbineClient):
    """
    This class implements the TDC GetEvents flow.
    Defaults to getting 10 events at a time.
    Specify a specific event_list_batch_no ID to get that batch again.
    Getting a batch again can only be done before we've ACK'ed it.
    """

    def get_events(self, event_list_batch_no=None, maximum_elements_returned=10):
        kwargs = {"maximum-elements-returned": maximum_elements_returned}

        if event_list_batch_no:
            kwargs["event-list-batch-no"] = event_list_batch_no

        # create the flow
        from columbine.models import Flow

        flow = Flow.objects.create(
            name="GetEventsFlow",
            reason=self.reason,
            source=self.source,
            references=self.references,
            parent_flow=self.parent_flow,
            kwargs=kwargs,
        )

        logger.info("Created new GetEventsFlow %s" % flow)
        return flow


class ShowCustomerSummaryClient(ColumbineClient):
    """
    A client to create a ShowCustomerSummary flow
    """

    def show_customer_summary(self, phone_no, zip_code=None, house_no=None):
        """
        Create flow to call ShowCustomerSummary
        """
        # prepare kwargs
        kwargs = {"phone-no": house_no}
        if zip_code:
            kwargs["zip-code"] = zip_code
        if house_no:
            kwargs["house-no"] = house_no

        # create the flow
        from columbine.models import Flow

        flow = Flow.objects.create(
            name="ShowCustomerSummaryFlow",
            reason=self.reason,
            source=self.source,
            references=self.references,
            parent_flow=self.parent_flow,
            kwargs=kwargs,
        )

        logger.info("Created new ShowCustomerSummaryFlow %s" % flow)
        return flow


class OrderClient(ColumbineClient):
    """
    The main *OrderFlow client.
    """

    def vula(
        self, street_name, house_no, zip_code, city=None, floor=None, door_no=None
    ):
        """
        Create flow to create a VULA order
        """
        # prepare kwargs
        kwargs = {
            "street-name": street_name,
            "house-no": house_no,
            "zip-code": zip_code,
        }
        if floor:
            kwargs["floor"] = floor
        if door_no:
            kwargs["door-no"] = door_no

        # create the flow
        from columbine.models import Flow

        flow = Flow.objects.create(
            name="VULAOrderFlow",
            reason=self.reason,
            source=self.source,
            references=self.references,
            kwargs=kwargs,
        )
        logger.info("Created new VULAOrderFlow %s" % flow)
        return flow

    def fbsa(
        self, street_name, house_no, zip_code, city=None, floor=None, door_no=None
    ):
        """
        Create flow to create an FBSA order
        """
        # prepare kwargs
        kwargs = {
            "street-name": street_name,
            "house-no": house_no,
            "zip-code": zip_code,
        }
        if floor:
            kwargs["floor"] = floor
        if door_no:
            kwargs["door-no"] = door_no

        # create the flow
        from columbine.models import Flow

        flow = Flow.objects.create(
            name="FBSAOrderFlow",
            reason=self.reason,
            source=self.source,
            references=self.references,
            kwargs=kwargs,
        )
        logger.info("Created new FBSAOrderFlow %s" % flow)
        return flow

    def coax(
        self, street_name, house_no, zip_code, city=None, floor=None, door_no=None
    ):
        """
        Create flow to create a COAX order
        """
        # prepare kwargs
        kwargs = {
            "street-name": street_name,
            "house-no": house_no,
            "zip-code": zip_code,
        }
        if floor:
            kwargs["floor"] = floor
        if door_no:
            kwargs["door-no"] = door_no

        # create the flow
        from columbine.models import Flow

        flow = Flow.objects.create(
            name="COAXOrderFlow",
            reason=self.reason,
            source=self.source,
            references=self.references,
            kwargs=kwargs,
        )
        logger.info("Created new COAXOrderFlow %s" % flow)
        return flow
