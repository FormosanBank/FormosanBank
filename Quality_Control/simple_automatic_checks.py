import os

SIZE_DIFF_THRESHOLD = 50

# Check that every scraped file has a corresponding XML file
# Won't be used for every resource (e.g. the ILDRF dicts) 
def check_counts(scraped_path, XMLifyed_path):
    return os.listdir(scraped_path) == os.listdir(XMLifyed_path)

# Check that every scraped file has a corresponding XML file
# and that the size difference isn't above a specific threshold (TBD)
# Please note this will rely on using consisten naming conventions
def check_size_diff(scraped_path, XMLifyed_path):
    for scraped in os.listdir(scraped_path):
        xml = scraped.split("_")[:-1] + ['XML']
        xml = "_".join(xml)
        xml_file_path = os.path.join(XMLifyed_path, xml)
        scraped_file_path = os.path.join(scraped_path, scraped)

        if not os.path.exists():
            return False
        
        if abs(os.path.getsize(xml_file_path) - os.path.getsize(scraped_file_path)) > SIZE_DIFF_THRESHOLD:
            return False
    
    return True


def check_sentence_count():
    pass

def check_token_count():
    pass

def check_type_count():
    pass



def main():
    pass

if __name__ == "__main__":
    main()