from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
import requests
import csv
import os.path


class ScraperInterface(ABC):
    @abstractmethod
    def get_product_info(self, link_list):
        pass

    @abstractmethod
    def get_page_count(self, url):
        pass

    @abstractmethod
    def get_links(self, url, num, num2=1):
        pass


class WebScraper(ScraperInterface):
    def get_product_info(self, link_list: list) -> list:
        """
        Scrape (name, price, avalability, needle, composition) for specific product
        """
        all_products = []
        for link in link_list:
            data = requests.get(link).text
            soup = BeautifulSoup(data, "html.parser")
            # Scrape product information and store it in a dictionary
            all_products.append(
                {
                    "name": soup.find(class_="maintitle-holder").select("h1")[0].text.strip(),
                    "price": soup.find(class_="product-price").select("span")[1].text.strip(),
                    "avalability": soup.find(
                        id="ContentPlaceHolder1_upStockInfoDescription").select("span")[0].text.strip(),
                    "needle": soup.find(
                        id="pdetailTableSpecs").select("tr")[4].text.strip().replace("Nadelstärke", ""),
                    "composition": soup.find(
                        id="pdetailTableSpecs").select("tr")[3].text.strip().replace("Zusammenstellung", ""),
                }
            )
        return all_products

    def get_page_count(self, url: str) -> int:
        try:
            req = requests.get(url + str(1))
            soup = BeautifulSoup(req.text, "html.parser")
            page_count = soup.find(id="ContentPlaceHolder1_lblPaginaVanTop")
            return int(page_count.select("b")[1].text.strip())
        except ValueError:
            print("Could not get the page, Please check the given URL!!")
            exit(0)

    def get_links(self, url: str, num: int, num2: int = 1) -> list:
        """
        Scrape links from the website and store it in a list
        """
        all_links = []
        for page in range(num2, num):
            req = requests.get(url + str(page))
            soup = BeautifulSoup(req.text, "html.parser")
            titles = soup.find_all(
                class_="productlist-title gtm-product-impression")
            for i in range(0, len(titles)):
                all_links.append(
                    {
                        "name": titles[i].text.strip(),
                        "link": titles[i].find("a")["href"],
                    }
                )
        return all_links


class FileHandlerInterface(ABC):
    @abstractmethod
    def dict_to_csv(self, links, name):
        pass

    @abstractmethod
    def search_csv(self, filename, query):
        pass

    @abstractmethod
    def get_query_from_txt(self, file):
        pass


class FileHandler(FileHandlerInterface):
    def dict_to_csv(self, links: str, name: str) -> None:
        """
        Write results to CSV file
        """
        keys = links[0].keys()
        with open(name, "w", newline="", encoding="utf-8") as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(links)
        print("Results saved to CSV file")

    def search_csv(self, filename, query):
        """
        Looks for links in the CSV file for required products
        """
        result_links = []
        with open(filename, "r") as f:
            csv_file = csv.reader(f, delimiter=",")
            for row in csv_file:
                for item in query:
                    if item in row[0]:
                        result_links.append(row[1])
        return result_links

    def get_query_from_txt(self, file_path: str) -> list:
        """
        Get product to scrape based on input file
        """
        query_list = []
        with open(file_path, "r") as f:
            for line in f:
                query_list.append(line.strip())
        return query_list


def main():
    url = "https://www.wollplatz.de/wolle/?page="
    all_product_as_csv = "wollplatz.csv"

    web_scraper = WebScraper()
    file_handler = FileHandler()

    if not os.path.exists(all_product_as_csv):
        page_count = web_scraper.get_page_count(url)
        links = web_scraper.get_links(url, page_count)
        file_handler.dict_to_csv(links, all_product_as_csv)

    query = file_handler.get_query_from_txt("req_products.txt")
    links = file_handler.search_csv(all_product_as_csv, query)
    products = web_scraper.get_product_info(links)
    file_handler.dict_to_csv(products, "products.csv")


if __name__ == "__main__":
    main()
