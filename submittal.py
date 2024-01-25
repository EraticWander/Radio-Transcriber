from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


class ContestEntryBot:
    def __init__(self):
        self.share_url = None

    def get_share_url(self):
        return self.share_url

    def enter_contest(self, keyword):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            try:
                page.goto("https://campaign.aptivada.com/contest/1606924?embed=true&parent=https%253A%252F%252Fwww.iheartradio.ca%252Fvirginradio%252Fkelowna%252Fcontests%252Fvirgin-radio-s-100-000-destroy-your-debt-1.21030390")

                page.wait_for_load_state("load")

                # Enter Email
                page.fill('input[type="email"]', "joeygidda@gmail.com")

                # Click submit button
                submit_button_selector = ".submitEmailBtn.formBtn.themeBackgroundHoverable"
                page.click(submit_button_selector)
                page.wait_for_timeout(3000)
                
                # Check if the success class is present
                success_class_present = page.locator('.formField.type_advanced_keyword.success').is_visible()
                
                if not success_class_present:   
                    print ("no keyword, trying keyword") 
                    # Test keyword
                    page.fill('input[name="advanced_keyword"]', keyword)
                    # Click Keyword submit button
                    page.locator('.inputSubmitBtn').nth(5).click()
                    page.wait_for_timeout(1000)
                    # Wait for the appearance of the success or error class
                    page.wait_for_selector('.formField.type_advanced_keyword.success, .formField.type_advanced_keyword.error', state='attached')
                    success_class_present = page.locator('.formField.type_advanced_keyword.success').is_visible()

                if success_class_present:
                    print ("Keyword success")
                    # See if fields are already entered
                    fname_success = page.locator('.formField.type_user_first_name.success').is_visible()
                    lname_success = page.locator('.formField.type_user_last_name.success').is_visible()
                    city_success = page.locator('.formField.type_user_city.success').is_visible()
                    zip_success = page.locator('.formField.type_user_zip.success').is_visible()
                    phone_success = page.locator('.formField.type_user_phone.success').is_visible()
                    
                    # Insert all text field
                    if not fname_success:
                        page.fill('input[name="user_first_name"]', "Joey")
                    if not lname_success:
                        page.fill('input[name="user_last_name"]', "Gidda")
                    if not city_success:
                        page.fill('input[name="user_city"]', "West Kelowna")
                    if not zip_success:
                        page.fill('input[name="user_zip"]', "V1Z 4C5")
                    if not phone_success:
                        page.fill('input[name="user_phone"]', "250-859-1433")
                        
                    page.check('[name="terms_checkbox"]')
                    print ("entered all text boxes")

                    page.select_option('.type_input_dropdown select', "25-34")

                    # Enter Selector info
                    select_elements = page.query_selector_all('.type_input_dropdown select')

                    if len(select_elements) > 1:
                        select_elements[1].select_option("KELOWNA")
                        
                    print ("Set Select tags")
                    page.wait_for_timeout(1000)

                    # Get share URL
                    self.share_url = page.locator('.readonly').input_value()
                    print ("Got share URL")

                    # Click Submit Button
                    submit_button_selector = ".formBtn.goToStepBtn.goToStep3Btn.themeBackgroundHoverable"
                    page.click(submit_button_selector)
                    

                # Check if the error class is present
                error_class_present = page.locator('.formField.type_advanced_keyword.error').is_visible()
                if error_class_present:
                    print ("Keyword Failed")
                    self.share_url = "FAILED"
                    
            except PlaywrightTimeoutError:
                print ("Time out Error)")
                page.screenshot(path=f"screenshots/{keyword}-TIMEOUT.png", full_page=True)
                self.share_url = "FAILED"

            except Exception as e:
                print (e)
                page.screenshot(path=f"screenshots/{keyword}-{e}.png", full_page=True)
                self.share_url = "FAILED"

            finally:
                context.close()