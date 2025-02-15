from utils import fetch_repositories

if __name__ == "__main__":

    owner = "sitagomes"
    response = fetch_repositories(owner)

    print(response)
