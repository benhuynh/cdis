#Purpose: Creates an image of 10 plots for each basin of a given scene.
#Usage: Use setwd() to move to a directory in which the csvs are located for a given scene.
#Then, just run the script!
files <- list.files(pattern='*.csv')
csvlist <- lapply(files,read.csv)
names(csvlist) <- files
bandplot <- function(rbtable,name) {
  matplot(t(rbtable),col='forestgreen',pch=19,lty=1,lend=1,ylim=c(0,.5),type='p',cex.main=.8,xlab='Band Number',ylab='Reflectance Value',main=paste0('Reflectance by Band Number for ',name))
  lines(colMeans(rbtable),type='l',ylim=0:1,col='red',lwd=2)
}
png('image.png',width=1600,height=1200,res=125)
par(mfrow=c(2,5))
for(i in 1:10) {
  bandplot(as.data.frame(csvlist[i]),names(csvlist)[i])
}
dev.off()