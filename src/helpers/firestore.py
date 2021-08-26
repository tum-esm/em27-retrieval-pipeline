
from firebase_admin import firestore
from .validator import Validator
from tqdm import tqdm

class Firestore:
    client = firestore.client()

    @staticmethod
    def get_meta():
        """
        Return the meta document from firestore
        """
        doc = Firestore.client \
            .collection('meta').document('em27') \
            .get()
        assert doc.exists, 'meta document does not exist in database'
        return doc.to_dict()
    
    @staticmethod
    def get_day(date):
        """
        Return a specific days document from firestore
        """
        doc = Firestore.client \
            .collection('em27-days').document(date) \
            .get()
        assert doc.exists, f'day "{date}" does not exist in database'
        return doc.to_dict()

    @staticmethod
    def get_all_days():
        """
        Return all day documents from firestore
        """
        doc_refs = Firestore.client.collection('em27-days').stream()
        return [doc.to_dict() for doc in doc_refs]
    
    @staticmethod
    def set_meta(document):
        """
        1. Validate the format of the given meta document
        2. Add that meta document to firestore
        """
        Validator.meta(document)
        Firestore.client \
            .collection('meta').document('em27') \
            .set(document)

    @staticmethod
    def set_day(document):
        """
        1. Validate the format of the given day document
        2. Add that day document to firestore
        """
        Validator.day(document)
        Firestore.client \
            .collection('em27-days').document(document['date']) \
            .set(document)
    
    @staticmethod
    def rollback(meta, days):
        """
        Rollback the database:
        1. Remove all documents
        2. Add the given meta and day documents
        """
        print("removing documents ...")
        Firestore.client.collection('meta').document('em27').delete()
        for doc in tqdm(Firestore.client.collection('em27-days').stream()):
            doc.reference.delete()
        
        print("creating documents ...")
        Firestore.set_meta(meta)
        for day in tqdm(days):
            Firestore.set_day(day)

