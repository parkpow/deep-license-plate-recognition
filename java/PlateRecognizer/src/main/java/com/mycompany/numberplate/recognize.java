/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package com.mycompany.numberplate;

import java.io.File;
import java.io.FileWriter;
import kong.unirest.Unirest;
import kong.unirest.HttpResponse;
/**
 *
 * @author uzair
 */
public class recognize {
    public static void main(String[] args){
        String token = "66657e2170068c797227476c967b4137c18c1a8a";
        String file = "C:\\Users\\uzair\\Downloads\\Soren1.jpg";
        
        try{
            HttpResponse<String> response = Unirest.post("https://api.platerecognizer.com/v1/plate-reader/")
            .header("Authorization", "Token "+token)
            .field("upload", new File(file))
            .asString();
            System.out.println("Recognize:");
            System.out.println(response.getBody().toString());
        }
        catch(Exception e){
            System.out.println(e);
        }
        
        try{
            HttpResponse<String> response = Unirest.get("https://api.platerecognizer.com/v1/statistics/")
            .header("Authorization", "Token "+token)
            .asString();
            System.out.println("Usage:");
            System.out.println(response.getBody().toString());
        }
        catch(Exception e){
            System.out.println(e);
        }
    }
}
