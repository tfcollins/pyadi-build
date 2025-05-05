from pymongo import MongoClient
from minio import Minio

class MongoMetadataDatabase:

    username: str = 'admin'
    password: str = 'admin'
    address: str = 'localhost'
    port: int = 27017

    db_name: str = "cse_dev"
    
    def __init__(self, uri: str = None, db_name: str = None):
        if db_name is not None:
            self.db_name = db_name
        if uri is None:
            uri = f"mongodb://{self.username}:{self.password}@{self.address}:{self.port}/"            
        self.client = MongoClient(uri)
        self.db = self.client[self.db_name]

    def get_collection(self, collection_name: str):
        return self.db[collection_name]

    def close(self):
        self.client.close()

    def upload_metadata(self, collection_name: str, metadata: dict) -> str:
        """
        Upload metadata to a specified collection in the MongoDB database.
        
        :param collection_name: Name of the collection where metadata will be stored.
        :param metadata: Dictionary containing metadata to be uploaded.
        :return: The result of the insert operation.
        """
        collection = self.get_collection(collection_name)
        result = collection.insert_one(metadata)
        # Check if the insert was successful
        if result.acknowledged:
            return result.inserted_id
        else:
            raise Exception("Failed to insert metadata into the collection.")


class MinioStorage:

    username: str = 'NvulxUKCBb2PBwCQdnkF'
    password: str = 'fX1kiwCstsWwDIfhd2A2NNiv5hHnFdNvyWbcPYno'
    address: str = 'localhost'
    port: int = 9000
    bucket_name: str = "cse_dev"

    def __init__(self, uri: str = None, bucket_name: str = None):
        if uri is None:
            uri = f"{self.address}:{self.port}"
        print(f"Connecting to Minio at {uri} with bucket '{self.bucket_name}'")
        self.client = Minio(
            uri,
            access_key=self.username,
            secret_key=self.password,
            secure=False
        )
        if bucket_name is not None:
            self.bucket_name = bucket_name
        # Ensure the bucket exists
        found = self.client.bucket_exists(self.bucket_name)
        print(found)
        if not found:
            print(f"Bucket '{self.bucket_name}' created.")
            self.client.make_bucket(self.bucket_name)
        else:
            print(f"Bucket '{self.bucket_name}' already exists.")

    def upload_file(self, component: str, file_path: str, object_name: str) -> None:
        """
        Upload a file to the Minio storage.

        :param component: Component name to create a subdirectory in the bucket.
        :param file_path: Path to the file to be uploaded.
        :param object_name: Name of the object in the Minio bucket.
        """
        # Add subdirectory based on component
        if component:
            object_name = f"{component}/{object_name}"
        try:
            self.client.fput_object(
                self.bucket_name,
                object_name,
                file_path
            )
        except Exception as e:
            raise Exception(f"Failed to upload file to Minio: {str(e)}")