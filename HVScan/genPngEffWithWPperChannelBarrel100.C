#include <iostream>
#include <fstream>
#include <iomanip>
#include <vector>
#include <string>
#include <math.h>

Double_t fitfunc( Double_t* _x, Double_t* _par ){
  Double_t effmax = _par[0];
  Double_t S = _par[1];
  Double_t HV50 = _par[2];
  return effmax / (1.0 + TMath::Exp( S *( _x[0] - HV50 ) ) );//
}

Double_t amano(double hv,double S,double emax,double hv50 ){
  return emax / (1.0 + TMath::Exp( S *( hv - hv50 ) ) );
}
void genPngEffWithWPperChannelBarrel100(){
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
  
  //Being defined the variables and constants
  ifstream rollslist;
  const int P=200;
  ifstream runsData;
  TGraphErrors * hveff;
  float ex[runsAmmount]; 
  float HV[runsAmmount];
  float EFF[runsAmmount];
  float ERR[runsAmmount];
  float EXP[runsAmmount];
  float CLS[runsAmmount];
  ifstream rolls;
  string rollName;
  double parameters[3];//
  double wp;
  double effwp;
  double effWpDef;
  double clswp;
  double effknee;
  double knee;
  double slope50;
  double chi2;
  double hv50error;
  ifstream fitData;
  TCanvas *C1 = new TCanvas("C1","Efficiency VS HV",200,10,800,600);  
  TF1 *f1;
  float hvc[2];
  float wpCh[1];
  float effWpCh[1];
  float EFFc[2];
  float xmax=9.9;
  float xmin = 8.5;
  float x[P];
  float y[P];
  double wpDef;
  ifstream wpChannel;


  rolls.open("data/Barrel.txt");
  rolls>>rollName;      
  while (!rolls.eof()){
    cout<<rollName<<endl;
    //Being charged the working point per channel associated with the current roll
    /*wpChannel.open(("results/"+rollName+"/wpChannel.txt").c_str());
    wpChannel>>wpDef;
    cout<<"wpDef= "<<wpDef<<endl;
    wpChannel.close();
    */
    //Being charged the run data obtained for the current roll
    runsData.open(("results/"+rollName+"/runsData.txt").c_str());
    for (int n=0;n<runsAmmount;n++){
      runsData>>HV[n]>>EFF[n]>>ERR[n]>>EXP[n]>>CLS[n];     
    }
    runsData.close();
    ///////////////////////////////// The error in this cases is defined in this way,  this is something that must be improved  
    for(int n=0;n<runsAmmount;n++){
      ex[n] = 0.0001;      
    }
    
    for(n=0;n<runsAmmount;n++){
      if(ERR[n]==0.) ERR[n]=10.;
    }
    //////////////////////////////////////////////////////
    //Being charged the fit data obtained for the current roll
    hveff = new TGraphErrors(runsAmmount, HV, EFF, ex, ERR);
    fitData.open(("results/"+rollName+"/fitData.txt").c_str());
    fitData>>wp>>slope50>>parameters[0]>>parameters[2]>>chi2>>clswp>>effwp>>wpDef>>effWpDef>>hv50error;
    cout<<wp<<" "<<slope50<<" "<<parameters[0]<<" "<<parameters[2]<<" "<<chi2<<" "<<clswp<<"  "<<effwp<<endl;
    fitData.close();
    parameters[1]= - 4*slope50/parameters[0];
    f1 = new TF1("f1",fitfunc,8.5,9.9,3); //3 is the number of fit parameters    
    f1->SetParameter(0, parameters[0]);
    f1->SetParameter(1, parameters[1]);//
    f1->SetParameter(2, parameters[2]);//
    
    //Being made the plot of Working Point and Knee
    knee = wp - 0.100;
    effknee=amano(knee,parameters[1],parameters[0],parameters[2]);
    hvc[0]=wp - 0.100;
    hvc[1]=wp;
    EFFc[0]=effknee;
    EFFc[1]=effwp;
    TGraph *gr2 = new TGraph(2,hvc,EFFc);
    
    //Being made the plot of Working Point per Channel
    wpCh[0]=wpDef;
    effWpCh[0]=effWpDef;
    TGraph *gr4 = new TGraph(1,wpCh,effWpCh);
    
    //Being made the plot of the sigmoid
    for (int k=0; k<P; k++){
      x[k]=xmin+k*(xmax-xmin)/(P-1);
      y[k]=amano(x[k],parameters[1],parameters[0],parameters[2]);
    }
    TGraph *gr3 = new TGraph(200,x,y);
    
    //Being set plot parameters 
    TCanvas *c1 = new TCanvas("c1","Sigmoid",200,10,600,400);
    hveff->SetLineColor(kRed);
    hveff->SetMarkerStyle(20);
    hveff->SetMarkerSize(2.0);
    hveff->SetMinimum(-0.01);
    hveff->SetMaximum(110);
    TAxis *axis = hveff->GetXaxis();
    axis->SetLimits(8.5,9.9); 
    hveff->SetTitle(("Efficiency vs HV_Eff " + rollName).c_str());
    hveff->GetXaxis()->SetTitle("HV_Eff(kV)");
    hveff->GetYaxis()->SetTitle("Efficiency(%)");
    hveff->Draw("AP");   
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
    cout<<rollName<<endl;
    gSystem->mkdir(("results/"+rollName).c_str());
    c1->SaveAs(("results/"+rollName+"/EFFvsHV.png").c_str());
    c1->Clear();
    //}
    rolls>>rollName;
  }
  exit(0);
}
