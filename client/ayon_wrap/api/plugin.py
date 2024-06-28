
def is_wrap_instance(instance, log):
    if "wrap" not in instance.data["families"]:
        log.debug("Not a Wrap instance, skipping all")
        return False
    return True