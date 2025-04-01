from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/")
db = client['ootd_database']
outfits = db['outfits']
for item in outfits.find():
    print(item)
