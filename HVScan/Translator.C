#include <iostream>
#include <fstream>
#include <iomanip>
#include <vector>
#include <string>
#include <math.h>


void Translator(){
  //Being Calculated the number of runs from luigi's file
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
  luigi.close();
  

  // Being  generated rollYeff#a.txt from rollYeff#.txt
  ifstream ifile;
  ofstream ofile;
  for (int i=0;i<runsAmmount;i++){
    std::string s;
    std::stringstream out;
    out << i+1;
    s = out.str();
    ifile.open(("data/rollYeff_"+s+".txt").c_str());
    ofile.open(("data/rollYeff_"+s+"a.txt").c_str());
    string name;
    double a1,a2,a3,a4,a5,a6,a7,a8,a9,a10,a11,a12,a13,a14;
    int n=0;
    ifile>>name>>a1>>a2>>a3>>a4>>a5>>a6>>a7>>a8>>a9>>a10>>a11>>a12>>a13>>a14;
    while((!ifile.eof())&(n<2172)){
      cout<<n<<endl;
      ofile<<name<<" "<<a1<<" "<<a2<<" "<<a3<<" "<<a4<<endl;
      n++;
      cout<<n<<endl;
      ifile>>name>>a1>>a2>>a3>>a4>>a5>>a6>>a7>>a8>>a9>>a10>>a11>>a12>>a13>>a14;
    }
    ifile.close();
    ofile.close();
  }  
  exit(0);
}
