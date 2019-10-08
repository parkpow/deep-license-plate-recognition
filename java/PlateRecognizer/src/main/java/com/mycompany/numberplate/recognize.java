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
        // Get api key from https://app.platerecognizer.com/start/ and replace MY_API_KEY
        String token = "MY_API_KEY";
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
