Load markdown files from Elastic Path Docs site in a MongoDB Atlas Cluster. 
Look at the code in populate_db.py to see how to load the markdown files from different repos.
You can comment out the repos you don't want to load.


### How to get Started?


* Install the required dependencies:
```bash
python -m venv myenv
source myenv/bin/activate
python -m pip install -r requirements.txt   


deactivate
```

* Load VectorDB using the markdown files in the data directory
```bash
usage: populate_database.py [-h] [--chunk_size CHUNK_SIZE]

optional arguments:
  -h, --help                show this help message and exit
  --chunk_size CHUNK_SIZE   Size of the Chunks
```
Use the flag ```--reset``` to clear the database

Example:

```bash
python populate_db.py --chunk_size 2000 
```
- 

## Notes
- The chunk size is the size of the chunks to split the markdown files into.
- Make sure that your Mondo collection has the following index "vector_index"
```json
{
  "fields": [
    {
      "numDimensions": 1536,
      "path": "embedding",
      "similarity": "cosine",
      "type": "vector"
    },
    {
      "path": "source",
      "type": "filter"
    }
  ]
}
```

## Credit
A lot of this code comes from https://www.youtube.com/watch?v=2TJxpyO3ei4 
