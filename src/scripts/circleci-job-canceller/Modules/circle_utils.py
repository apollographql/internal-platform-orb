import requests
import pprint

go_back_page_limit = 5  # set me to None to go back ALL the way, which you'll need to do once (only?)

def get_all_items(relative_url, headers):
    url = f"https://circleci.com/api/v2{relative_url}"
    temp_url = str(url)
    pages_iterated = 0
    while True:
        res = requests.get(temp_url, headers=headers).json()
        try:
            yield from res["items"]  # delegates iteration to the (list), so returns 1 by one...
        except KeyError as e:
            print(e)
            pprint.pprint(res)
            print(url)
            raise e
        page_token = res.get("next_page_token")
        if page_token is not None:
            temp_url = f"{url}?page-token={page_token}"
            pages_iterated += 1
        else:
            break

        if (go_back_page_limit and (pages_iterated >= go_back_page_limit)):
            print("page limit hit")
            break
