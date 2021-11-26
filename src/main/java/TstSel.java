import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.util.Iterator;
import java.util.List;
import java.util.stream.Collectors;

public class TstSel {

   public static void main(String[] args) {
      WebDriver wDriver = getHoldingsDriver();
      try {
         wDriver.get("https://nb.fidelity.com/public/nb/default/home");
         By plusPlanLink = By.cssSelector(
               "#client-employer a[aria-Label='IBM 401(K) PLUS PLAN Summary.']");
         new WebDriverWait(wDriver, 45)
               .until(ExpectedConditions.elementToBeClickable(plusPlanLink));
         WebElement lnk = wDriver.findElement(plusPlanLink);
         ((JavascriptExecutor) wDriver).executeScript("arguments[0].click();", lnk);
         lnk = new WebDriverWait(wDriver, 8)
               .until(ExpectedConditions.elementToBeClickable(By.cssSelector(
                     "#holdings-section .show-details-link")));
         ((JavascriptExecutor) wDriver).executeScript("arguments[0].click();", lnk);

         String dateShown = wDriver.findElement(By.id("modal-header--holdings"))
               .findElement(By.xpath("./following-sibling::*")).getText();
         System.out.println(dateShown);
         WebElement hTbl = wDriver.findElement(By.id("holdingsTable"));
         List<String> tHdrs = hTbl.findElements(By.cssSelector("thead > tr > th"))
               .stream().map(WebElement::getText).collect(Collectors.toList());
         System.out.println("Headers:" + tHdrs);
         Iterator<WebElement> bodyRows = hTbl.findElements(By.cssSelector("tbody > tr")).iterator();

         while (bodyRows.hasNext()) {
            String hldgName = bodyRows.next().findElement(By.tagName("a")).getText();
            List<String> rowCols = bodyRows.next().findElements(By.tagName("td"))
                  .stream().map(WebElement::getText).collect(Collectors.toList());
            System.out.println(hldgName + ':' + rowCols);
         }
      }
      catch (Exception e) {
         System.err.println("oops");
         e.printStackTrace(System.err);
      }
      finally {
         wDriver.quit();
      }

   } // end main(String[])

   private static WebDriver getHoldingsDriver() {
      ChromeOptions crOpts = new ChromeOptions();
      crOpts.addArguments("user-data-dir="
            + "C:/Users/John/AppData/Local/VSCode/Chrome/User Data");

      return new ChromeDriver(crOpts);
   } // end getHoldingsDriver()

} // end class TstSel
