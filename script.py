import pandas as pd
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
import os
import argparse
from dotenv import load_dotenv

#load webdriver and environment variables
driver = webdriver.Edge()
load_dotenv()

#function to get urls from csv
def get_urls(csvFile, header):
    df = pd.read_csv(csvFile)
    try:
        urls = df[header]
    except KeyError:
        urls = df.iloc[:, 0]
    return urls

#function to login
def login(driver):
    driver.get("https://www.linkedin.com/login")
    username = driver.find_element(By.ID, "username")
    password = driver.find_element(By.ID, "password")
    USERNAME1 = os.getenv("LINKEDIN_USER")
    PASSWORD1 = os.getenv("LINKEDIN_PASS")
    username.send_keys(USERNAME1)
    password.send_keys(PASSWORD1)
    password.send_keys(Keys.RETURN)
    #could be minimised if no need of manual verification
    time.sleep(5)  

#function to scroll so that every elements loads properly and elements can be found
def scroll_page(driver):
    total_height = driver.execute_script("return document.body.scrollHeight")
    for i in range(10):
        driver.execute_script(f"window.scrollTo(0, {i * total_height/10})")
        time.sleep(0.5)
    time.sleep(2)

#function to get name
def get_name(driver, wait, profile_data):
    try:
        name_element = wait.until(EC.presence_of_element_located((By.XPATH, "//h1")))
        profile_data["Name"] = name_element.text
        print(f"Name: {profile_data['Name']}")
    except Exception as e:
        profile_data["Name"] = "N/A"
        print(f"Error getting name: {e}")

#function to get bio
def get_bio(driver, wait, profile_data):
    try:
        bio_element = driver.find_element(By.XPATH, "//div[@class='text-body-medium break-words']")
        profile_data["Bio"] = bio_element.text
        print(f"Bio: {profile_data['Bio']}")
    except:
        profile_data["Bio"] = "N/A"
        print("User has no bio")    

#function to detect if there is a show all button and expanding all experiences
def expandExp(driver):
    try:
        if "/details/experience/" in driver.current_url:
            return True
        
        try:
            experience_section = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//section[.//div[text()='Experience' or text()='experience']]"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", experience_section)
            time.sleep(1)
        except:
            print("Experience section not found by section/heading")
            try:
                experience_headers = driver.find_elements(By.XPATH, "//h2[contains(text(), 'Experience')]")
                if experience_headers:
                    section = experience_headers[0].find_element(By.XPATH, "./ancestor::section")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", section)
                    time.sleep(1)
            except:
                print("Experience section not found by h2 heading either")
                return False
        
        show_all_xpaths = [
            "//span[contains(text(), 'Show all')]/ancestor::button",
            "//span[contains(text(), 'Show all')]/ancestor::a",
            "//a[contains(text(), 'Show all')]",
            "//button[contains(text(), 'Show all')]",
            "//a[contains(text(), 'experiences')]",
            "//button[contains(text(), 'experiences')]",
            "//a[contains(@aria-label, 'Show all experiences')]",
            "//button[contains(@aria-label, 'Show all experiences')]"
        ]
        
        for xpath in show_all_xpaths:
            try:
                buttons = driver.find_elements(By.XPATH, xpath)
                for button in buttons:
                    button_text = button.text.lower()
                    if 'experience' in button_text:
                        print(f"Found 'Show all experiences' button: {button_text}")
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                        time.sleep(1)
                        try:
                            WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                            button.click()
                        except ElementClickInterceptedException:
                            driver.execute_script("arguments[0].click();", button)
                        print("Successfully clicked 'Show all experiences' button")
                        time.sleep(5)  
                        return True
            except Exception as e:
                print(f"Error with xpath {xpath}: {e}")
                continue
                
        try:
            result = driver.execute_script("""
                var buttons = document.querySelectorAll('button, a');
                for(var i=0; i<buttons.length; i++) {
                    if(buttons[i].textContent.toLowerCase().includes('show all') && 
                       buttons[i].textContent.toLowerCase().includes('experience')) {
                        buttons[i].click();
                        return true;
                    }
                }
                return false;
            """)
            if result:
                print("Successfully clicked 'Show all experiences' button using JavaScript")
                time.sleep(5)
                return True
        except Exception as e:
            print(f"JavaScript click error: {e}")

        print("No 'Show all experiences' button found or clicked, will try to extract from main profile")
        return False
    except Exception as e:
        print(f"Error expanding experiences: {e}")
        return False

#function to scrape experience information in a structured manner
def extrExp(driver):
    experience_list = []
    
    try:
        is_details_page = "/details/experience/" in driver.current_url
        
        if is_details_page:
            try:
                time.sleep(3)  
                experience_entries = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//li[contains(@class, 'pvs-list__item--line-separated')]"))
                )
                
                for entry in experience_entries:
                    try:
                        text_elements = entry.find_elements(By.XPATH, ".//span[@aria-hidden='true']")
                        if len(text_elements) >= 2:
                            role = text_elements[0].text.strip()
                            company = text_elements[1].text.strip()
                            experience_list.append(f"{company}: {role}")
                    except Exception as e:
                        print(f"Error extracting experience entry: {e}")
                        continue
            except Exception as e:
                print(f"Error extracting from details page: {e}")

        else:
            try:
                experience_sections = driver.find_elements(By.XPATH, "//section[.//div[text()='Experience' or text()='Work Experience']]")
                if not experience_sections:
                    experience_sections = driver.find_elements(By.XPATH, "//section[.//h2[contains(text(), 'Experience')]]")
                
                if experience_sections:
                    experience_section = experience_sections[0]
                    experience_entries = experience_section.find_elements(By.XPATH, ".//li[contains(@class, 'pvs-list__item--line-separated')]")
                    
                    for entry in experience_entries:
                        try:
                            text_elements = entry.find_elements(By.XPATH, ".//span[@aria-hidden='true']")
                            if len(text_elements) >= 2:
                                role = text_elements[0].text.strip()
                                company = text_elements[1].text.strip()
                                experience_list.append(f"{company}: {role}")
                            else:
                                if text_elements:
                                    role_company = text_elements[0].text.strip()
                                    experience_list.append(role_company)
                        except Exception as e:
                            print(f"Error extracting experience entry: {e}")
                            continue
            except Exception as e:
                print(f"Error extracting from main profile: {e}")
        
        if not experience_list:
            try:
                experience_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'experience-item')]")
                for element in experience_elements:
                    try:
                        text = element.text.strip()
                        if text:
                            parts = text.split('\n')
                            if len(parts) >= 2:
                                role = parts[0]
                                company = parts[1]
                                experience_list.append(f"{company}: {role}")
                    except:
                        continue
            except Exception as e:
                print(f"Error in fallback extraction: {e}")
    
    except Exception as e:
        print(f"Error in extract_experience: {e}")
    
    return experience_list

#function to expand education section 
def expand_education(driver):
    try:
        if "/details/education/" in driver.current_url:
            return True
        
        try:
            education_section = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//section[.//div[text()='Education' or text()='education']]"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", education_section)
            time.sleep(1)
        except:
            try:
                education_headers = driver.find_elements(By.XPATH, "//h2[contains(text(), 'Education')]")
                if education_headers:
                    section = education_headers[0].find_element(By.XPATH, "./ancestor::section")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", section)
                    time.sleep(1)
            except:
                print("Education section not found by h2 heading either")
                return False
        
        show_all_xpaths = [
            "//a[contains(text(), 'Show all')]",
            "//button[contains(text(), 'Show all')]",
            "//a[contains(text(), 'education')]",
            "//button[contains(text(), 'education')]",
            "//a[contains(@aria-label, 'Show all education')]",
            "//button[contains(@aria-label, 'Show all education')]"
        ]
        
        for xpath in show_all_xpaths:
            try:
                buttons = driver.find_elements(By.XPATH, xpath)
                for button in buttons:
                    button_text = button.text.lower()
                    if 'education' in button_text:
                        print(f"Found 'Show all education' button: {button_text}")
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                        time.sleep(1)
                        try:
                            WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                            button.click()
                        except ElementClickInterceptedException:
                            driver.execute_script("arguments[0].click();", button)
                        print("Successfully clicked 'Show all education' button")
                        time.sleep(5)  
                        return True
            except Exception as e:
                print(f"Error with xpath {xpath}: {e}")
                continue
                
        try:
            result = driver.execute_script("""
                var buttons = document.querySelectorAll('button, a');
                for(var i=0; i<buttons.length; i++) {
                    if(buttons[i].textContent.toLowerCase().includes('show all') && 
                       buttons[i].textContent.toLowerCase().includes('education')) {
                        buttons[i].click();
                        return true;
                    }
                }
                return false;
            """)
            if result:
                print("Successfully clicked 'Show all education' button using JavaScript")
                time.sleep(5)
                return True
        except Exception as e:
            print(f"JavaScript click error: {e}")

        print("No 'Show all education' button found or clicked, will try to extract from main profile")
        return False
    except Exception as e:
        print(f"Error expanding education: {e}")
        return False

#function to extract education information and store it in a proper way
def extract_education(driver):
    education_list = []
    
    try:
        is_details_page = "/details/education/" in driver.current_url
        
        if is_details_page:
            try:
                time.sleep(3)  
                education_entries = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//li[contains(@class, 'pvs-list__item--line-separated')]"))
                )
                
                for entry in education_entries:
                    try:
                        text_elements = entry.find_elements(By.XPATH, ".//span[@aria-hidden='true']")
                        if len(text_elements) >= 2:
                            university = text_elements[0].text.strip()
                            degree = text_elements[1].text.strip()
                            education_list.append(f"{university}: {degree}")
                    except Exception as e:
                        print(f"Error extracting education entry: {e}")
                        continue
            except Exception as e:
                print(f"Error extracting from details page: {e}")

        else:
            try:
                education_sections = driver.find_elements(By.XPATH, "//section[.//div[text()='Education' or text()='education']]")
                if not education_sections:
                    education_sections = driver.find_elements(By.XPATH, "//section[.//h2[contains(text(), 'Education')]]")
                
                if education_sections:
                    education_section = education_sections[0]
                    education_entries = education_section.find_elements(By.XPATH, ".//li[contains(@class, 'pvs-list__item--line-separated')]")
                    
                    for entry in education_entries:
                        try:
                            text_elements = entry.find_elements(By.XPATH, ".//span[@aria-hidden='true']")
                            if len(text_elements) >= 2:
                                university = text_elements[0].text.strip()
                                degree = text_elements[1].text.strip()
                                education_list.append(f"{university}: {degree}")
                            else:
                                if text_elements:
                                    university_degree = text_elements[0].text.strip()
                                    education_list.append(university_degree)
                        except Exception as e:
                            print(f"Error extracting education entry: {e}")
                            continue
            except Exception as e:
                print(f"Error extracting from main profile: {e}")
        
        if not education_list:
            try:
                education_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'education-item')]")
                for element in education_elements:
                    try:
                        text = element.text.strip()
                        if text:
                            parts = text.split('\n')
                            if len(parts) >= 2:
                                university = parts[0]
                                degree = parts[1]
                                education_list.append(f"{university}: {degree}")
                    except:
                        continue
            except Exception as e:
                print(f"Error in fallback education extraction: {e}")
    
    except Exception as e:
        print(f"Error in extract_education: {e}")
    
    return education_list

#function to expand the certifications section by looking for anchor tags with the text "Show all"/"Show all certifications" using x path and taking care of expanding them
def expand_certifications(driver):
    try:
        if "/details/certifications/" in driver.current_url:
            return True
        
        try:
            certifications_section = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//section[.//div[text()='Licenses & certifications' or text()='Licenses & certifications']]"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", certifications_section)
            time.sleep(1)
        except:
            try:
                certifications_headers = driver.find_elements(By.XPATH, "//h2[contains(text(), 'Licenses & certifications')]")
                if certifications_headers:
                    section = certifications_headers[0].find_element(By.XPATH, "./ancestor::section")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", section)
                    time.sleep(1)
            except:
                return False
        
        show_all_xpaths = [
            "//a[contains(text(), 'Show all')]",
            "//button[contains(text(), 'Show all')]",
            "//a[contains(text(), 'certifications')]",
            "//button[contains(text(), 'certifications')]",
            "//a[contains(@aria-label, 'Show all licenses & certifications')]",
            "//button[contains(@aria-label, 'Show all licenses & certifications')]"
        ]
        
        for xpath in show_all_xpaths:
            try:
                buttons = driver.find_elements(By.XPATH, xpath)
                for button in buttons:
                    button_text = button.text.lower()
                    if 'Show all licenses & certifications' in button_text:
                        print(f"Found 'Show all certifications' button: {button_text}")
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                        time.sleep(1)
                        try:
                            WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                            button.click()
                        except ElementClickInterceptedException:
                            driver.execute_script("arguments[0].click();", button)
                        print("Successfully clicked 'Show all licenses & certifications' button")
                        time.sleep(5)  
                        return True
            except Exception as e:
                print(f"Error with xpath {xpath}: {e}")
                continue
                
        try:
            result = driver.execute_script("""
                var buttons = document.querySelectorAll('button, a');
                for(var i=0; i<buttons.length; i++) {
                    if(buttons[i].textContent.toLowerCase().includes('show all') && buttons[i].textContent.toLowerCase().includes('licenses') &&
                       buttons[i].textContent.toLowerCase().includes('certifications')) {
                        buttons[i].click();
                        return true;
                    }
                }
                return false;
            """)
            if result:
                print("Successfully clicked 'Show all licenses & certifications' button using JavaScript")
                time.sleep(5)
                return True
        except Exception as e:
            print(f"JavaScript click error: {e}")

        print("No 'Show all licenses & certifications' button found or clicked, will try to extract from main profile")
        return False
    except Exception as e:
        print(f"Error expanding licenses & certifications: {e}")
        return False

#scrapes data from the certifications section for both details page and main profile
def extract_certifications(driver):
    certifications_list = []
    
    try:
        is_details_page = "/details/certifications/" in driver.current_url
        
        if is_details_page:
            try:
                time.sleep(3)  
                certification_entries = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//li[contains(@class, 'pvs-list__item--line-separated')]"))
                )
                
                for entry in certification_entries:
                    try:
                        text_elements = entry.find_elements(By.XPATH, ".//span[@aria-hidden='true']")
                        if len(text_elements) >= 2:
                            certification = text_elements[0].text.strip()
                            issuer = text_elements[1].text.strip()
                            certifications_list.append(f"{certification}: {issuer}")
                    except Exception as e:
                        print(f"Error extracting certification entry: {e}")
                        continue
            except Exception as e:
                print(f"Error extracting from details page: {e}")

        else:
            try:
                certifications_sections = driver.find_elements(By.XPATH, "//section[.//div[text()='Licenses & certifications' or text()='Licenses & certifications']]")
                if not certifications_sections:
                    certifications_sections = driver.find_elements(By.XPATH, "//section[.//h2[contains(text(), 'Licenses & certifications')]]")
                
                if certifications_sections:
                    certifications_section = certifications_sections[0]
                    certifications_entries = certifications_section.find_elements(By.XPATH, ".//li[contains(@class, 'pvs-list__item--line-separated')]")
                    
                    for entry in certifications_entries:
                        try:
                            text_elements = entry.find_elements(By.XPATH, ".//span[@aria-hidden='true']")
                            if len(text_elements) >= 2:
                                certification = text_elements[0].text.strip()
                                issuer = text_elements[1].text.strip()
                                certifications_list.append(f"{certification}: {issuer}")
                            else:
                                if text_elements:
                                    certification_issuer = text_elements[0].text.strip()
                                    certifications_list.append(certification_issuer)
                        except Exception as e:
                            print(f"Error extracting certification entry: {e}")
                            continue
            except Exception as e:
                print(f"Error extracting from main profile: {e}")
        
        if not certifications_list:
            try:
                certifications_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'certification-item')]")
                for element in certifications_elements:
                    try:
                        text = element.text.strip()
                        if text:
                            parts = text.split('\n')
                            if len(parts) >= 2:
                                certification = parts[0]
                                issuer = parts[1]
                                certifications_list.append(f"{certification}: {issuer}")
                    except:
                        continue
            except Exception as e:
                print(f"Error in fallback certification extraction: {e}")
    
    except Exception as e:
        print(f"Error in extract_certifications: {e}")
    
    return certifications_list

#converts the list of experience entries into a dictionary for easy access
def toDictionary(experience_list):
    """Processing Results"""
    experience_dict = {}
    for exp in experience_list:
        if ":" in exp:
            company, role = exp.split(":", 1)
            experience_dict[company.strip()] = role.strip()
        else:
            experience_dict[exp] = ""
    return experience_dict

#saves result in csv file format
def saveToCSV(results, output_prefix):
    results_df = pd.DataFrame(results)
    output_file = f"{output_prefix}.csv"
    results_df.to_csv(output_file, index=False)
    print(f"\nScraped {len(results)} profiles and saved to {output_file}")

#saves results in json format
def saveToJSON(results, output_prefix):
    output_file = f"{output_prefix}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=4)
    print(f"Also saved results as {output_file}")

#main function
def main(input_file, url_header, output_prefix): #input_file, url_header, output_prefix are command line arguments used to make the script more dynamic and user-friendly, more given about them in read me
    #getting urls from the input file
    urls = get_urls(input_file, url_header)
    #logging into linkedin using the login function and waiting for the page to load and manual verification(if needed)(won't work headlessly if requires manual verification, LinkedIn only allows a few daily sessions)
    login(driver)
    print("Log in successfull, waiting for page to load/manual verification")
    time.sleep(8)

    #creating a list to store the results for each profile from the csv
    results = []

    #iterating through the urls present in the column of the input CSV file
    for url in urls:
        try:
            driver.get(url) #opens the profile page
            print(f"Successfully loaded: {url}")
            
            time.sleep(6) #waits for the page to load completely 
            scroll_page(driver) #ensures that each and every component of the page is loaded completely
            profile_data = {"URL": url}
            
            #main block that extracts information from the profile
            try:
                #creating a wait object as it was required for explicit waits
                wait = WebDriverWait(driver, 10)
                
                print("Extracting name and bio...")
                #this function will execute to extract the NAME from the profile page
                get_name(driver, wait, profile_data)
                #this function will execute to extract the BIO from the profile page
                get_bio(driver, wait, profile_data)

                #EXPERIENCE
                print("Extracting experience information...")
                #checks if the experience section is expandable and calls the function to expand it if required
                isExpandable = expandExp(driver)

                #statement to check if the experience section is expandable, if it is then waits for 3.5 seconds to full load the new page and calls the function to extract experience information
                if isExpandable:
                    time.sleep(3.5)  
                    experience_list = extrExp(driver)
                
                #otherwise if the experience section is not expandable then calls the function to extract experience information
                else:
                    experience_list = extrExp(driver)
                
                #if the experience list is not empty then stores the experience information in a dictionary using the toDictionary function
                if experience_list:
                    profile_data["Experience"] = toDictionary(experience_list)
                
                #otherwise if the experience list is empty then stores an empty dictionary to mantain consistency
                else:
                    profile_data["Experience"] = {}
                    print("Could not extract experience information")

                #EDUCATION
                print("Extracting education information...")

                #navigate back to profile page
                driver.get(url)
                #checks if the education section is expandable and calls the function to expand it if required, the expand_education function returns true if the section is expandable and false otherwise
                isExpandableForEducation = expand_education(driver)
                #statement to check if the education section is expandable, if it is then waits for 3.5 seconds to full load the new page and calls the function to extract education information-this is govenerned by the below if statement
                if isExpandableForEducation:
                    time.sleep(3.5)
                    education_list = extract_education(driver)
                #otherwise if the education section is not expandable then calls the function to extract education information
                else:
                    education_list = extract_education(driver)
                
                #if the education list is not empty then stores the education information in a dictionary using the toDictionary function and makes sure that the dictionary is not empty with the else statement
                if education_list:
                    profile_data["Education"] = toDictionary(education_list)
                else:
                    profile_data["Education"] = {}
                    print("Could not extract education information")


                #CERTIFICATIONS
                #navigate back to profile page
                driver.get(url)
                #checks if the certifications section is expandable and calls the expand_certifications function to expand it if required
                isExpandableForCertifications = expand_certifications(driver)
                if isExpandableForCertifications:
                    time.sleep(3.5) #waits for 3.5 seconds to completely load the new page
                    certifications_list = extract_certifications(driver)
                else:
                    certifications_list = extract_certifications(driver) #just scrapes from the profile page as no expansion is required
                    
                #if the certifications list is not empty then stores the certifications information in a dictionary using the toDictionary function
                if certifications_list:
                    profile_data["Certification"] = toDictionary(certifications_list)
                else:
                    profile_data["Certification"] = {} #stores an empty dictionary to mantain consistency
                    print("Could not extract certification information")
                
                results.append(profile_data)

            #error handling for the main block to check that all the information is extracted
            except Exception as e:
                print(f"Error extracting profile data: {e}")
                profile_data["Name"] = "Error"
                profile_data["Experience"] = {}
                profile_data["Education"] = {}
                profile_data["Certification"] = {}
                results.append(profile_data)
                continue

        except TimeoutException: #error handling for when the page takes too long to load
            print(f"Timeout while loading: {url}")
        except NoSuchElementException: #error handling when the element cant be found
            print(f"Element not found on: {url}")
        except Exception as e: #general error handling for any other error 
            print(f"An error occurred while processing {url}: {e}")

    #closes the driver
    print("Closing driver...")
    driver.quit()

    #saves the results to a CSV and JSON file, for easier analysis and easy data manipulation
    saveToCSV(results, output_prefix)
    saveToJSON(results, output_prefix)


if __name__ == "__main__":
    print("-x-x-x-Program Started-x-x-x-")
    print("Welcome to the LinkedIn Profile Scraper")
    print("This program scrapes LinkedIn profiles for name, bio, experience, education, and certifications.")

    # Parsing command line arguments and calling the main function
    parser = argparse.ArgumentParser(description="LinkedIn Profile Scraper")
    parser.add_argument("--input", required=True, help="Input CSV file containing LinkedIn profile URLs") #the input file is required
    parser.add_argument("--output", default="results", help="Output file prefix for CSV and JSON files") #the output file prefix is optional
    parser.add_argument("--url-header", default="url", help="Header name for the URL column in the CSV") #the url header is optional, default is set to url for smoother usage make sure that header name in the csv file matches "url" or set it manually
    args = parser.parse_args()

    # Check if the input file exists
    if not os.path.isfile(args.input):
        print(f"Error: Input file '{args.input}' does not exist.")
        exit(1)

    print("Starting program...")
    main(args.input, args.url_header, args.output)
    print("-x-x-x-Program Executed-x-x-x-")