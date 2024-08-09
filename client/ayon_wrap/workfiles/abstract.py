import os


class FileItem:
    """File item that represents a file.

    Can be used for both Workarea and Published workfile. Workarea file
    will always exist on disk which is not the case for Published workfile.

    Args:
        dirpath (str): Directory path of file.
        filename (str): Filename.
        modified (float): Modified timestamp.
        created_by (Optional[str]): Username.
        representation_id (Optional[str]): Representation id of published
            workfile.
        filepath (Optional[str]): Prepared filepath.
        exists (Optional[bool]): If file exists on disk.
    """

    def __init__(
        self,
        dirpath,
        filename,
        modified,
        created_by=None,
        updated_by=None,
        representation_id=None,
        filepath=None,
        exists=None
    ):
        self.filename = filename
        self.dirpath = dirpath
        self.modified = modified
        self.created_by = created_by
        self.updated_by = updated_by
        self.representation_id = representation_id
        self._filepath = filepath
        self._exists = exists

    @property
    def filepath(self):
        """Filepath of file.

        Returns:
            str: Full path to a file.
        """

        if self._filepath is None:
            self._filepath = os.path.join(self.dirpath, self.filename)
        return self._filepath

    @property
    def exists(self):
        """File is available.

        Returns:
            bool: If file exists on disk.
        """

        if self._exists is None:
            self._exists = os.path.exists(self.filepath)
        return self._exists

    def to_data(self):
        """Converts file item to data.

        Returns:
            dict[str, Any]: File item data.
        """

        return {
            "filename": self.filename,
            "dirpath": self.dirpath,
            "modified": self.modified,
            "created_by": self.created_by,
            "representation_id": self.representation_id,
            "filepath": self.filepath,
            "exists": self.exists,
        }

    @classmethod
    def from_data(cls, data):
        """Re-creates file item from data.

        Args:
            data (dict[str, Any]): File item data.

        Returns:
            FileItem: File item.
        """

        required_keys = {
            "filename",
            "dirpath",
            "modified",
            "representation_id"
        }
        missing_keys = required_keys - set(data.keys())
        if missing_keys:
            raise KeyError("Missing keys: {}".format(missing_keys))

        return cls(**{
            key: data[key]
            for key in required_keys
        })
