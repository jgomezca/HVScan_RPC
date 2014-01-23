#include <iostream>
#include <fstream>
#include <iomanip>
#include <vector>
#include <string>
#include <math.h>

Double_t expFunc(Double_t* _x, Double_t* _par){
  return  TMath::Exp(_par[0]+_x[0]*_par[1]);
}

Double_t expFuncAMano(double hv, double A, double B){
   return TMath::Exp(A + hv*B);
}


Double_t fitfunc( Double_t* _x, Double_t* _par ){
  Double_t effmax = _par[0];
  Double_t S = _par[1];
  Double_t HV50 = _par[2];
  return effmax / (1.0 + TMath::Exp( S *( _x[0] - HV50 ) ) );//
}

Double_t amano(double hv,double S,double emax,double hv50 ){
  return emax / (1.0 + TMath::Exp( S *( hv - hv50 ) ) );
}

Double_t difamano(double hv, double S, double emax, double hv50){
  return -emax*S*TMath::Exp(S*(hv-hv50))/((1.0 + TMath::Exp( S *( hv - hv50 ) ) )*(1.0 + TMath::Exp( S *( hv - hv50 ) ) )) ;
}


void FitEndCap120(){
  //Being calculated the number of runs from luigi's file
  string line;
  ifstream luigi;
  luigi.open("data/luigi.txt");
  if(!luigi){
    cout<<"WARNING luigi.txt do not exist"<<endl;
  }
  cout<<"Reading Luigis file"<<endl;
  int l=0;
  while(!luigi.eof()){
    getline(luigi,line);
    l++;
  }
  const int runsAmmount = l-1;
  cout<<runsAmmount<<endl;
  
  //Being defined the variables and constants
  const double resolution = 0.01;
  string rollName;
  ifstream rolls;
  ifstream runsData;
  float ex[runsAmmount];
  float ecls[runsAmmount];
  float HV[runsAmmount];
  float EFF[runsAmmount];
  float ERR[runsAmmount];
  float EXP[runsAmmount];
  float CLS[runsAmmount];
  float hv[runsAmmount-3];
  float cls[runsAmmount-3];
  float exc[runsAmmount-3];
  float ecls[runsAmmount-3];
  double parameters[3];//
  double wp;
  double effwp;
  double effknee;
  double knee;
  double effkneemin;
  double clswp;
  double clswpDef;
  double ca;
  double cb;
  double slope50;
  double chi2;
  double chi2CLS;
  ofstream fitData;
  ofstream fitDataCLS;
  double wpDef;
  double effWpDef;
  double hv50error;
  ifstream wpChannel;
  bool bfitCLS=false;
  f1 = new TF1("f1",fitfunc,8.5,9.9,3); //3 es el numero de parametros del fit//
  f2 = new TF1("f2",expFunc,8.5,9.9,2);
  rolls.open("data/EndCap.txt");
 
  //Being read the data, made the fit and stored the information obtained
  rolls>>rollName;
  while (!rolls.eof()){
    cout<<rollName<<endl;
    //Being read the point of operation of the channel
    wpChannel.open(("results/"+rollName+"/wpChannel.txt").c_str());
    wpChannel>>wpDef;
    cout<<"wpDef= "<<wpDef<<endl;
    wpChannel.close();
    
    //Being configured the seed of the fit parameters
    const char init = rollName[0];
    f1->SetParameter(0, 95.0);
    if (init=='R'){
      f1->SetParameter(1, -12);//
      f1->SetParameter(2, 9.3);//
    }
    else{
      f1->SetParameter(1, -8.5);//
      f1->SetParameter(2, 8.9);//
    }      
    f2->SetParameter(0,-14);
    f2->SetParameter(1,1.5);
    
    //Being read the data for the current roll
    runsData.open(("results/"+rollName+"/runsData.txt").c_str());
    for (int n=0;n<runsAmmount;n++){
      runsData>>HV[n]>>EFF[n]>>ERR[n]>>EXP[n]>>CLS[n];
      cout<<HV[n]<<" "<<EFF[n]<<" "<<ERR[n]<<" "<<EXP[n]<<" "<<CLS[n]<<endl;
      //The first three points (with lower high voltage) are not taking in account in the proccess of doing the CLS fit (because their lower efficiency
      if (n>2){
	hv[n-3]=HV[n];
	cls[n-3]=CLS[n];
	cout<<hv[n-3]<<endl;
	cout<<cls[n-3]<<endl;
	if (cls[n-3]!=0) bFitCLS=true;
      }
      
    }
    runsData.close();


    ///////////////////////////////// The error in the CLS fit is done by hand,  it is something to be improved  
    for(int n=0;n<runsAmmount;n++){
      ex[n] = 0.0001;
      if (n>2){
	exc[n-3]=0.0001;
	ecls[n-3] = 0.0001;
      }
    }
    
    for(n=0;n<runsAmmount;n++){
      if(ERR[n]==0.) ERR[n]=10.;
    }
    //////////////////////////////////////////////////////

   
  
    //Being made the HV fit
    hveff = new TGraphErrors(runsAmmount, HV, EFF, ex, ERR);
    hveff->Fit(f1);
    chi2=(f1->GetChisquare())/runsAmmount;
    effmaxerror=(f1->GetParError(0));
    Serror=(f1->GetParError(1));
    hv50error=(f1->GetParError(2));
    parameters[0]=f1->GetParameter(0);
    parameters[1]=f1->GetParameter(1);//
    parameters[2]=f1->GetParameter(2);//
    for(i=0;i<3;i++) cout<<"parameter "<< i<<" = "<<parameters[i]<<endl;
   
    //Being calculated the knee and the proposed working point for this roll
    wp=0;
    effwp=0;
    effknee=0;
    knee=parameters[2];
    effkneemin = parameters[0]*0.95;
    if ((parameters[0]>0)&&(parameters[1]<0)){//In this case is not calculated because the fit is wrong
      while (effknee<effkneemin){
	cout<<rollName<<" "<<effknee<<" "<<effkneemin<<" "<<parameters[0]<<" "<<parameters[1]<<" "<<parameters[2]<<endl;
	knee=knee+resolution;
	effknee=amano(knee,parameters[1],parameters[0],parameters[2]);       
      }
    }    
    wp= knee +0.120;
    effwp=amano(wp,parameters[1],parameters[0],parameters[2]);
    effWpDef=amano(wpDef,parameters[1],parameters[0],parameters[2]);
    cout<<"EFFWPChannel "<<effWpDef<<endl;
    
    //Being done the CLS fit
    hvcls = new TGraphErrors(runsAmmount-3, hv, cls, exc, ecls);
    if (bFitCLS)  hvcls->Fit(f2);
    ca=f2->GetParameter(0);
    cb=f2->GetParameter(1);
    cout<<"Fit CLS done: "<<ca<<" "<<cb<<endl;
    clswp = expFuncAMano(wp,ca,cb);
    clsknee = expFuncAMano(knee,ca,cb);
    clsWpDef = expFuncAMano(wpDef,ca,cb);
    chi2CLS=(f2->GetChisquare())/(runsAmmount-3);
    slope50 = difamano(parameters[2],parameters[1],parameters[0],parameters[2]);
    fitData.open(("results/"+rollName+"/fitData.txt").c_str());
   
    //Being stored the resulting data
    fitData<<wp<<" "<<slope50<<" "<<parameters[0]<<" "<<parameters[2]<<" "<<chi2<<" "<<clswp<<" "<<effwp<<" "<<wpDef<<" "<<effWpDef<<" "<<clsWpDef<<" "<<effmaxerror<<" "<<Serror<<" "<<hv50error<<" "<<parameters[1]<<endl;
    fitData.close();
    fitDataCLS.open(("results/"+rollName+"/fitDataCLS.txt").c_str());    
    fitDataCLS<<ca<<" "<<cb<<" "<<chi2CLS<<" "<<wp<<" "<<clswp<<" "<<wpDef<<" "<<clsWpDef<<endl;
    fitDataCLS.close();
    rolls>>rollName;    
  }  
  exit(0);
}
