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

void genPngClsExpBarrel100(){
  //Being calculated the number of rolls from luigi's file
  string line;
  ifstream rollslist;
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
  
  //Being defined the variables and constants
  const int P=200;
  ifstream runsData;
  TGraphErrors * hvcls;
  const int runsHavingInAccount = runsAmmount -3;
  float ex[runsAmmount]; 
  float HV[runsAmmount];
  float EFF[runsAmmount];
  float ERR[runsAmmount];
  float EXP[runsAmmount];
  float CLS[runsAmmount];
  float hv[runsHavingInAccount];
  float cls[runsHavingInAccount];
  float exc[runsHavingInAccount];
  float ecls[runsHavingInAccount];
  ifstream rolls;
  string rollName;
  double ca,cb;
  double chi2,wp,clswp;
  double knee,clsknee;
  ifstream fitData;
  TCanvas *c1 = new TCanvas("C1","CLS VS HV",200,10,800,600);  
  TF1 *f1;
  float wpCh[1];
  float clsWpCh[1];
  float hvc[2];
  float CLSc[2];
  float xmax=9.9;
  float xmin = 8.5;
  float x[P];
  float y[P];
  double wpDef;
  double clsWpDef;
  ifstream wpChannel;
  
  rolls.open("data/Barrel.txt");
  rolls>>rollName;      
  while (!rolls.eof()){
    //Being charged the working point per channel associated with the current roll
    /*    wpChannel.open(("results/"+rollName+"/wpChannel.txt").c_str());
    wpChannel>>wpDef;
    cout<<"wpDef= "<<wpDef<<endl;
    wpChannel.close();
    */
    //Being charged the run data for the current roll
    runsData.open(("results/"+rollName+"/runsData.txt").c_str());
    for (int n=0;n<runsAmmount;n++){
      runsData>>HV[n]>>EFF[n]>>ERR[n]>>EXP[n]>>CLS[n];
      //The first three runs (lower high voltage) are not plotted
      if (n>2){
	hv[n-3]=HV[n];
	cls[n-3]=CLS[n];
      }
    }
    runsData.close();

    ///////////////////////////////// The error in this cases is defined in this way,  this is something that must be improved    
    for(int n=0;n<runsAmmount;n++){
      if (n>2){
	exc[n-3]=0.0001;
	ecls[n-3] = 0.0001;
      }
    }
    
    //////////////////////////////////////////////////////
    //Being charged the fit data obtained for the current roll
    hvcls = new TGraphErrors(runsHavingInAccount, hv, cls, exc, ecls);
    cout<<rollName;
    fitData.open(("results/"+rollName+"/fitDataCLS.txt").c_str());
    fitData>>ca>>cb>>chi2>>wp>>clswp>>wpDef>>clsWpDef;
    cout<<ca<<" "<<cb<<" "<<wp<<" "<<clswp<<endl;
    fitData.close();
    f1 = new TF1("f1",expFunc,8.5,9.9,2); //3 es el numero de parametros del fit//
    f1->SetParameter(0, ca);
    f1->SetParameter(1, cb);//
    
    //Being made the plot of Working Point and Knee  
    knee = wp - 0.100;
    clsknee=expFuncAMano(knee,ca,cb);
    hvc[0]=wp - 0.100;
    hvc[1]=wp;
    CLSc[0]=clsknee;
    CLSc[1]=clswp;
    TGraph *gr2 = new TGraph(2,hvc,CLSc);
    
    //Being made the plot of Working Point per Channel
    wpCh[0]=wpDef;
    clsWpCh[0]=clsWpDef;
    TGraph *gr4 = new TGraph(1,wpCh,clsWpCh);
    
    //Being made the plot of the sigmoid
    for (int k=0; k<P; k++){
      x[k]=xmin+k*(xmax-xmin)/(P-1);
      y[k]=expFuncAMano(x[k],ca,cb);
      x[k]=x[k];
    }
    TGraph *gr3 = new TGraph(200,x,y);
   
    
    //Being set plot parameters 
    hvcls->SetLineColor(kRed);
    hvcls->SetMarkerStyle(20);
    hvcls->SetMarkerSize(2.0);
    hvcls->SetMinimum(-0.01);
    hvcls->SetMaximum(6);
    TAxis *axis = hvcls->GetXaxis();
    axis->SetLimits(8.5,9.9); 
    hvcls->SetTitle(("CLS vs HV_Eff " + rollName).c_str());
    hvcls->GetXaxis()->SetTitle("HV_Eff(kV)");
    hvcls->GetYaxis()->SetTitle("CLS");
    hvcls->Draw("AP");   
    gr3->SetLineColor(kBlue);
    gr3->Draw("C");// superimpose the second graph by leaving out the axis option "A"
    gr2->SetMarkerStyle(28);
    gr2->SetMarkerSize(3);
    gr2->SetLineColor(kBlue);
    gr2->Draw("P");
    gr4->SetMarkerStyle(24);
    gr4->SetMarkerSize(5);
    gr4->SetLineColor(kRed);
    gr4->Draw("P");
    
    //Being stored the plot as png file
    gSystem->mkdir(("results/"+rollName).c_str());
    c1->SaveAs(("results/"+rollName+"/CLSvsHV.png").c_str());
    c1->Clear();     
    //}
    rolls>>rollName;
  }
  exit(0);
}
