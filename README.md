Load MD files from Elastic Path Docs site in a MongoDB Atlas Cluster

### How to get Started?


* Install the required dependencies:
```bash
python -m venv myenv
source myenv/bin/activate
python -m pip install -r requirements.txt   


deactivate
```

* Load VectorDB using the PDFs in the data directory
```bash
usage: populate_database.py [-h] [--reset] [--data_path DATA_PATH] [--chunk_size CHUNK_SIZE]

optional arguments:
  -h, --help                show this help message and exit
  --reset                   Reset the database.
  --data_path DATA_PATH     The path to the data directory.
  --chunk_size CHUNK_SIZE   Size of the Chunks
```
Use the flag ```--reset``` to clear the database

Example:

```bash
python populate_db.py --reset --data_path ./data_md/docs/commerce-manager --chunk_size 2000 
```
- 

## Credit
A lot of this code comes from https://www.youtube.com/watch?v=2TJxpyO3ei4 
