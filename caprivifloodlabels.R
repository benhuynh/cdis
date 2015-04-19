#Usage: scrapes all available Caprivi flood data from GDACS
library(RCurl)
library(XML)
xdata1 <- getURL('http://old.gdacs.org/flooddetection/data.aspx?from=20010114&to=20150305&type=html&alertlevel=green&datatype=4DAYS&areaid=14950')
table1 <- readHTMLTable(xdata1)
table1 <- as.data.frame(table1)
hypscenes <- read.csv("~/hypscenes.csv")
hypscenes$Acquisition.Date <- as.Date(hypscenes$Acquisition.Date,format='%m/%d/%Y')
table1$Acquisition.Date <- as.Date(table1$NULL.RecordDate,format='%m/%d/%Y')
table2 <- merge(table1,hypscenes,by='Acquisition.Date')
table3 <- table2[c('Acquisition.Date','NULL.SignalAvg','NULL.MagnitudeAvg','Entity.ID')]
colnames(table3) <- c('Date','SignalMean','MagnitudeMean','SceneID')
table3$MagnitudeMean <- as.numeric(as.character(table3$MagnitudeMean))
for(i in 1:134) {
  if(table3$MagnitudeMean[i] >= 0) {
    table3$FloodLabel[i] <- 1
  }
  else {
    table3$FloodLabel[i] <- 0
  }
}


