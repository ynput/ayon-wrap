"""
Requires:
    instance.data["families"] containing "wrap"

Provides:
    instance.data["publish"] set to False for secondary instances
"""
import pyblish.api

from ayon_wrap.api.plugin import is_wrap_instance


class CollectProductName(pyblish.api.ContextPlugin):
    """Mark secondary instances with same product_name as not publishable.

    There is `ValidateProductUniqueness` validator that checks for unique
    product names. There could be use case in Wrap workfile for multiple
    writers having same product name, but different output extension.

    Extractor will then merge all secondary (coming after first one) into
    single one with multiple representations.
    """
    order = pyblish.api.CollectorOrder - 0.5
    label = "Collect Wrap Unique Products"
    hosts = ["traypublisher"]

    optional = False
    active = True

    def process(self, context):
        product_name_to_instance = {}
        for instance in context:
            is_wrap = is_wrap_instance(instance, self.log)
            if not is_wrap:
                return

            product_name = instance.data["productName"]
            another_instance = product_name_to_instance.get(product_name)
            if another_instance is not None:
                self.log.debug(f"{product_name} already exist, skipping.")
                instance.data["publish"] = False
            else:
                product_name_to_instance[product_name] = instance
