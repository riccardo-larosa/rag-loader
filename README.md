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
* Clone the repo you want to load into your local machine
```bash
git clone git@<url>:<repo>.git
```

* Load VectorDB using the markdown files that you want to load (for openapi specs see below)
```bash
usage: populate_database.py [-h] [--doc_site DOC_SITE] [--repo_location REPO_LOCATION] [--chunk_size CHUNK_SIZE]

optional arguments:
  -h, --help                show this help message and exit
  --doc_site DOC_SITE   The name of the docs site, i.e.:EPCC or EPSM
  --repo_location REPO_LOCATION   The location on your local machine of the repo where the files are located
  --chunk_size CHUNK_SIZE   Size of the Chunks (default to 3000)
```

Example:

```bash
python populate_db.py --doc_site EPCC --repo_location ~/tmp_ep_dev --chunk_size 3000 
```

* Load OpenAPI specs files from a directory
```bash
usage: populate_openapi_db.py [-h] [--openapi_dir_location OPENAPI_DIR_LOCATION]

optional arguments:
  -h, --help                show this help message and exit
  --openapi_dir_location OPENAPI_DIR_LOCATION   The location on your local machine of the repo where the files are located
```

Example:

```bash
python populate_openapi_db.py --openapi_dir_location ~/tmp_ep_dev/openapispecs
```

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
