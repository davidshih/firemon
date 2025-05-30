#!/usr/bin/env python3
"""
FireMon Policy Optimizer Automation Script

This script automates the process of:
1. Opening FireMon Policy Optimizer
2. Processing first two PO tickets
3. Finding policy revision changes
4. Taking screenshots of specific rule changes
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import time
import os
from datetime import datetime
import logging
import argparse
from dotenv import load_dotenv

class FireMonAutomation:
    def __init__(self, url, username, password, headless=False, browser="chrome"):
        self.url = url
        self.username = username
        self.password = password
        self.headless = headless
        self.browser = browser.lower()
        self.driver = None
        self.wait = None
        self.screenshot_dir = "screenshots"
        self.setup_logging()
        self.setup_directories()
        
    def setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('firemon_automation.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_directories(self):
        """Create necessary directories"""
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)
            self.logger.info(f"Created screenshot directory: {self.screenshot_dir}")
    
    def initialize_driver(self):
        """Initialize WebDriver (Chrome or Edge)"""
        try:
            if self.browser == "edge":
                return self._initialize_edge_driver()
            else:
                return self._initialize_chrome_driver()
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.browser} driver: {str(e)}")
            # Try fallback browser
            if self.browser == "chrome":
                self.logger.info("Trying Edge as fallback...")
                self.browser = "edge"
                return self._initialize_edge_driver()
            elif self.browser == "edge":
                self.logger.info("Trying Chrome as fallback...")
                self.browser = "chrome"
                return self._initialize_chrome_driver()
            return False
    
    def _initialize_chrome_driver(self):
        """Initialize Chrome WebDriver"""
        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            if self.headless:
                chrome_options.add_argument('--headless')
            
            try:
                # Try with webdriver-manager first
                self.driver = webdriver.Chrome(
                    service=ChromeService(ChromeDriverManager().install()), 
                    options=chrome_options
                )
            except Exception as e:
                self.logger.warning(f"WebDriver manager failed: {e}")
                # Try with system chromedriver
                self.logger.info("Trying system chromedriver...")
                self.driver = webdriver.Chrome(options=chrome_options)
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 20)
            self.logger.info("Chrome WebDriver initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Chrome driver: {str(e)}")
            raise e
    
    def _initialize_edge_driver(self):
        """Initialize Edge WebDriver"""
        try:
            edge_options = webdriver.EdgeOptions()
            edge_options.add_argument('--start-maximized')
            edge_options.add_argument('--disable-blink-features=AutomationControlled')
            edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            edge_options.add_experimental_option('useAutomationExtension', False)
            
            if self.headless:
                edge_options.add_argument('--headless')
            
            try:
                # Try with webdriver-manager first
                self.driver = webdriver.Edge(
                    service=EdgeService(EdgeChromiumDriverManager().install()), 
                    options=edge_options
                )
            except Exception as e:
                self.logger.warning(f"WebDriver manager failed: {e}")
                # Try with system msedgedriver
                self.logger.info("Trying system msedgedriver...")
                self.driver = webdriver.Edge(options=edge_options)
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 20)
            self.logger.info("Edge WebDriver initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Edge driver: {str(e)}")
            raise e
    
    def login(self):
        """Login to FireMon"""
        try:
            self.logger.info(f"Navigating to FireMon: {self.url}")
            self.driver.get(self.url)
            time.sleep(3)
            
            # Try multiple common selectors for username field
            username_selectors = ["#username", "#user", "[name='username']", "[name='user']"]
            username_field = None
            
            for selector in username_selectors:
                try:
                    username_field = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except:
                    continue
                    
            if not username_field:
                raise Exception("Could not find username field")
                
            username_field.clear()
            username_field.send_keys(self.username)
            self.logger.info("Username entered")
            
            # Try multiple common selectors for password field
            password_selectors = ["#password", "#pass", "[name='password']", "[name='pass']"]
            password_field = None
            
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
                    
            if not password_field:
                raise Exception("Could not find password field")
                
            password_field.clear()
            password_field.send_keys(self.password)
            self.logger.info("Password entered")
            
            # Try multiple common selectors for login button
            login_selectors = ["#login-button", "#login", "[type='submit']", "button[type='submit']"]
            login_button = None
            
            for selector in login_selectors:
                try:
                    login_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
                    
            if not login_button:
                raise Exception("Could not find login button")
                
            login_button.click()
            self.logger.info("Login button clicked")
            
            time.sleep(5)
            self.logger.info("Login successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            return False
    
    def navigate_to_policy_optimizer(self):
        """Navigate to Policy Optimizer"""
        try:
            # Try multiple ways to find Policy Optimizer link
            po_selectors = [
                "//a[contains(text(), 'Policy Optimizer')]",
                "//a[contains(text(), 'policy optimizer')]",
                "//a[contains(text(), 'PO')]",
                "//span[contains(text(), 'Policy Optimizer')]/..",
                "[href*='policy-optimizer']",
                "[href*='po']"
            ]
            
            po_link = None
            for selector in po_selectors:
                try:
                    if selector.startswith("//"):
                        po_link = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    else:
                        po_link = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    break
                except:
                    continue
                    
            if not po_link:
                raise Exception("Could not find Policy Optimizer link")
                
            po_link.click()
            self.logger.info("Clicked Policy Optimizer link")
            time.sleep(5)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to navigate to Policy Optimizer: {str(e)}")
            return False
    
    def get_po_tickets(self):
        """Get first two PO tickets"""
        try:
            # Try different selectors for PO tickets
            ticket_selectors = [".po-ticket", ".ticket", ".policy-ticket", "[class*='ticket']"]
            po_tickets = []
            
            for selector in ticket_selectors:
                try:
                    po_tickets = self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
                    if po_tickets:
                        break
                except:
                    continue
                    
            if not po_tickets:
                raise Exception("Could not find PO tickets")
                
            self.logger.info(f"Found {len(po_tickets)} PO tickets")
            return po_tickets[:2]  # Return first two tickets
            
        except Exception as e:
            self.logger.error(f"Failed to get PO tickets: {str(e)}")
            return []
    
    def extract_ticket_info(self, tickets):
        """Extract rule names and revision links from tickets"""
        tickets_info = []
        
        for i, ticket in enumerate(tickets):
            try:
                # Try different selectors for rule name
                rule_name_selectors = [".rule-name", ".name", "[class*='rule']", "[class*='name']"]
                rule_name = None
                
                for selector in rule_name_selectors:
                    try:
                        rule_name_element = ticket.find_element(By.CSS_SELECTOR, selector)
                        rule_name = rule_name_element.text.strip()
                        if rule_name:
                            break
                    except:
                        continue
                        
                if not rule_name:
                    rule_name = f"Rule_{i+1}"  # Fallback name
                    
                # Try different selectors for revision link
                revision_selectors = [".policy-revision-link", ".revision-link", "[href*='revision']", "a"]
                revision_link = None
                
                for selector in revision_selectors:
                    try:
                        revision_link = ticket.find_element(By.CSS_SELECTOR, selector)
                        break
                    except:
                        continue
                        
                if revision_link:
                    tickets_info.append({
                        'index': i,
                        'rule_name': rule_name,
                        'revision_link': revision_link
                    })
                    self.logger.info(f"Ticket {i+1}: Rule name = {rule_name}")
                else:
                    self.logger.warning(f"Could not find revision link for ticket {i+1}")
                    
            except Exception as e:
                self.logger.error(f"Failed to extract info from ticket {i+1}: {str(e)}")
                
        return tickets_info
    
    def process_tickets(self, tickets_info):
        """Process each ticket and take screenshots"""
        for ticket_info in tickets_info:
            try:
                self.logger.info(f"\nProcessing ticket {ticket_info['index']+1}: {ticket_info['rule_name']}")
                
                main_window = self.driver.current_window_handle
                
                # Click revision link
                ticket_info['revision_link'].click()
                self.logger.info("Clicked policy revision link")
                
                # Switch to new window
                time.sleep(2)
                for window_handle in self.driver.window_handles:
                    if window_handle != main_window:
                        self.driver.switch_to.window(window_handle)
                        break
                
                time.sleep(3)
                
                # Find and click view changes button
                if self.click_view_changes():
                    self.capture_rule_screenshot(ticket_info)
                else:
                    self.logger.warning("Could not click view changes button")
                    self.take_fallback_screenshot(ticket_info)
                
                # Close tab and return to main window
                self.driver.close()
                self.driver.switch_to.window(main_window)
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Error processing ticket {ticket_info['index']+1}: {str(e)}")
                try:
                    self.driver.switch_to.window(main_window)
                except:
                    pass
    
    def click_view_changes(self):
        """Click the view changes toggle button"""
        try:
            view_changes_selectors = [
                "//button[contains(text(), 'View Changes')]",
                "//button[contains(text(), 'view changes')]",
                "//button[contains(text(), 'Show Changes')]",
                ".view-changes-toggle",
                "#view-changes",
                "[class*='view-changes']",
                "[class*='toggle']"
            ]
            
            for selector in view_changes_selectors:
                try:
                    if selector.startswith("//"):
                        view_changes_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    else:
                        view_changes_btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    
                    view_changes_btn.click()
                    self.logger.info("Clicked 'View Changes' button")
                    time.sleep(5)  # Wait for changes to load
                    return True
                except:
                    continue
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to click view changes: {str(e)}")
            return False
    
    def capture_rule_screenshot(self, ticket_info):
        """Capture screenshot of matching rule changes"""
        try:
            # Try different selectors for rule rows
            row_selectors = [".rule-change-row", ".rule-row", ".change-row", "[class*='rule'][class*='row']"]
            rule_rows = []
            
            for selector in row_selectors:
                try:
                    rule_rows = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if rule_rows:
                        break
                except:
                    continue
                    
            self.logger.info(f"Found {len(rule_rows)} rule change rows")
            
            found_matching_rule = False
            for row in rule_rows:
                try:
                    # Try to find rule name in row
                    name_selectors = [".rule-name", ".name", "[class*='name']"]
                    row_rule_name = None
                    
                    for selector in name_selectors:
                        try:
                            name_element = row.find_element(By.CSS_SELECTOR, selector)
                            row_rule_name = name_element.text.strip()
                            if row_rule_name:
                                break
                        except:
                            continue
                    
                    if row_rule_name and row_rule_name == ticket_info['rule_name']:
                        self.logger.info(f"Found matching rule: {row_rule_name}")
                        
                        # Scroll to element
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", row)
                        time.sleep(1)
                        
                        # Take screenshot
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        screenshot_name = f"{self.screenshot_dir}/PO_ticket_{ticket_info['index']+1}_{ticket_info['rule_name']}_{timestamp}.png"
                        row.screenshot(screenshot_name)
                        self.logger.info(f"Screenshot saved: {screenshot_name}")
                        
                        found_matching_rule = True
                        break
                        
                except Exception as e:
                    self.logger.warning(f"Error processing row: {str(e)}")
                    continue
            
            if not found_matching_rule:
                self.take_fallback_screenshot(ticket_info)
                
        except Exception as e:
            self.logger.error(f"Failed to capture rule screenshot: {str(e)}")
            self.take_fallback_screenshot(ticket_info)
    
    def take_fallback_screenshot(self, ticket_info):
        """Take full page screenshot as fallback"""
        try:
            self.logger.warning(f"Taking full page screenshot for: {ticket_info['rule_name']}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_name = f"{self.screenshot_dir}/PO_ticket_{ticket_info['index']+1}_full_page_{timestamp}.png"
            self.driver.save_screenshot(screenshot_name)
            self.logger.info(f"Full page screenshot saved: {screenshot_name}")
        except Exception as e:
            self.logger.error(f"Failed to take fallback screenshot: {str(e)}")
    
    def run(self):
        """Main execution method"""
        try:
            self.logger.info("Starting FireMon automation...")
            
            if not self.initialize_driver():
                return False
                
            if not self.login():
                return False
                
            if not self.navigate_to_policy_optimizer():
                return False
                
            tickets = self.get_po_tickets()
            if not tickets:
                return False
                
            tickets_info = self.extract_ticket_info(tickets)
            if not tickets_info:
                self.logger.error("No valid tickets found")
                return False
                
            self.process_tickets(tickets_info)
            
            self.logger.info("\n=== AUTOMATION COMPLETE ===")
            self.logger.info(f"Screenshots saved in: {self.screenshot_dir}")
            
            # List screenshots
            screenshots = [f for f in os.listdir(self.screenshot_dir) if f.endswith('.png')]
            self.logger.info(f"Total screenshots captured: {len(screenshots)}")
            for screenshot in screenshots:
                self.logger.info(f"  - {screenshot}")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Automation failed: {str(e)}")
            return False
            
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("Browser closed")

def main():
    # Load environment variables
    load_dotenv()
    
    parser = argparse.ArgumentParser(description='FireMon Policy Optimizer Automation')
    parser.add_argument('--url', default=os.getenv('FIREMON_URL'), help='FireMon URL')
    parser.add_argument('--username', default=os.getenv('FIREMON_USERNAME'), help='Username')
    parser.add_argument('--password', default=os.getenv('FIREMON_PASSWORD'), help='Password')
    parser.add_argument('--browser', choices=['chrome', 'edge'], default='chrome', help='Browser to use (chrome or edge)')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    
    args = parser.parse_args()
    
    if not all([args.url, args.username, args.password]):
        print("Error: URL, username, and password are required")
        print("Set them as arguments or in .env file")
        return 1
    
    automation = FireMonAutomation(args.url, args.username, args.password, args.headless, args.browser)
    
    if automation.run():
        print("Automation completed successfully!")
        return 0
    else:
        print("Automation failed!")
        return 1

if __name__ == "__main__":
    exit(main())