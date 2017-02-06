To sign the extension, create a directory "MXI", and unzip the .zxp file into it.
Then run (ucf.jar is from Adobe's signing toolkit):

java -jar ucf.jar -package -storetype PKCS12 -keystore path/to/signing/cert -tsa http://timestamp.entrust.net/TSS/JavaHttpTS SgTkPhotoshopEngine.zxp -C "./MXI" .
