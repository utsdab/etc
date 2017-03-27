//Maya ASCII 2016 scene
//Name: animation.ma
//Last modified: Sun, Aug 30, 2015 03:32:22 PM
//Codeset: 1252
requires maya "2016";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2016";
fileInfo "version" "2016";
fileInfo "cutIdentifier" "201502261600-953408";
fileInfo "osv" "Microsoft Windows 8 Business Edition, 64-bit  (Build 9200)\n";
createNode animCurveTU -n "CURVE1";
	rename -uid "FDB20CA0-4833-C0F0-9B4C-3491B79DC0A5";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 5 10 5;
createNode animCurveTU -n "CURVE2";
	rename -uid "8E1BA6DB-4D95-9192-B655-239DB1F46D3E";
	setAttr ".tan" 9;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 1 10 1;
	setAttr -s 2 ".kot[0:1]"  5 5;
createNode animCurveTU -n "CURVE3";
	rename -uid "16862CD9-49B0-EEE7-E228-E79BA1C73B5F";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0.25 10 0.42958527814637792;
createNode animCurveTU -n "CURVE4";
	rename -uid "47CEAC7C-4410-3FB3-367C-D9BC9B8AA9CB";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0.5 10 0.85917055629275585;
createNode animCurveTA -n "CURVE5";
	rename -uid "8894E180-488C-2D8D-482E-7C9BDF5DFAFA";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 45 10 30.81018202226841;
createNode animCurveTA -n "CURVE6";
	rename -uid "259D8F20-4677-BF9D-23EF-B384E78B9509";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 90 10 149.70880463068096;
createNode animCurveTL -n "CURVE7";
	rename -uid "0A3E1605-40F6-F97A-6E6B-AD859F102FEA";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0 10 0;
createNode animCurveTL -n "CURVE8";
	rename -uid "D453652F-487B-F223-80B4-F39D74BFBC30";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 8 10 8;
createNode animCurveTL -n "CURVE9";
	rename -uid "EC6E4505-478E-08EF-A103-F4BB1236AEB8";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 -12 10 11.214436147065292;
createNode animCurveTU -n "CURVE10";
	rename -uid "01841554-48D6-5AD5-C340-988040404BD2";
	setAttr ".tan" 9;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 1 10 1;
	setAttr -s 2 ".kot[0:1]"  5 5;
createNode animCurveTU -n "CURVE11";
	rename -uid "2B7678B5-43B6-12A7-B337-FDB774CF4918";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0.666 10 0.666;
createNode animCurveTU -n "CURVE12";
	rename -uid "B298A623-4597-36DC-7A88-DF8AFFF3BB50";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0 10 10;
createNode animCurveTU -n "CURVE13";
	rename -uid "1368F7F6-43B1-385C-2893-0F8B83FE11FF";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0.2 10 0.2;
createNode animCurveTU -n "CURVE14";
	rename -uid "9FF0335F-4E6C-919E-E611-BBA78127C10B";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 1.4 10 1.4;
createNode animCurveTU -n "CURVE15";
	rename -uid "C10D3BE7-4311-02E1-BEB8-908F34FC3405";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 2.6 10 2.6;
createNode animCurveTU -n "CURVE16";
	rename -uid "C754C79E-4E9E-CC4B-C7FC-27814A461FA6";
	setAttr ".tan" 9;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 1 10 1;
	setAttr -s 2 ".kot[0:1]"  5 5;
createNode animCurveTL -n "CURVE18";
	rename -uid "63067628-4726-F685-7FEA-A5B1F0420287";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0 10 15;
// End