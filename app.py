from selenium import webdriver
import time
import urllib.parse

numbers = ["905355961046", "905355961046"]
message = urllib.parse.quote("Merhaba! Etkinliğimiz başlıyor 🚀")

driver = webdriver.Chrome()
driver.get("https://web.whatsapp.com")
input("QR kodu taradıktan sonra Enter’a bas...")

for num in numbers:
    driver.get(f"https://web.whatsapp.com/send?phone={num}&text={message}")
    time.sleep(5)
    try:
        send_btn = driver.find_element("xpath", '//span[@data-icon="send"]')
        send_btn.click()
        time.sleep(3)
    except:
        print(f"{num} gönderilemedi.")
