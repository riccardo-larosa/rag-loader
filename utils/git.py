import git
import shutil
from git import RemoteProgress
import os

def clone_repo(git_repo_url, temp_repo_path="~/temp_repo"):
    
    class Progress(RemoteProgress):
        def update(self, op_code, cur_count, max_count=None, message=''):
            print(f'\rProgress: {cur_count}/{max_count} {message}', end='')
    
    try:
        temp_repo_path = os.path.expanduser(temp_repo_path)
        # Clean up directory if it exists
        if os.path.exists(temp_repo_path):
            print(f"Cleaning up existing directory: {temp_repo_path}")
            shutil.rmtree(temp_repo_path)
        print(f"Cloning {git_repo_url} into {temp_repo_path}")
        git.Repo.clone_from(
            git_repo_url, 
            temp_repo_path,
            progress=Progress(),
            depth=None  
        )

        print(f"\n✅ Repository cloned successfully in {temp_repo_path}")
        
    except Exception as e:
        print(f"❌ Clone failed: {e}")
        return False

    return True



def delete_repo(temp_repo_path):
    if os.path.exists(temp_repo_path):
        print(f"Cleaning up existing directory: {temp_repo_path}")
        shutil.rmtree(temp_repo_path)

