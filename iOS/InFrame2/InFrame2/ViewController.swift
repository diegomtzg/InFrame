//
//  ViewController.swift
//  InFrame2
//
//  Created by Ike Kilinc on 4/21/20.
//  Copyright © 2020 Ike Kilinc. All rights reserved.
//

import UIKit

class ViewController: UIViewController {
    
    // IDLE, DISPLAYING, TRACKING
    var state = "IDLE"
    
    @IBOutlet weak var frameView: UIImageView!
    @IBOutlet weak var instructionLabel: UILabel!
    @IBOutlet weak var requestButton: UIButton!
    @IBOutlet weak var bottomButton: UIButton!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        // Do any additional setup after loading the view.
    }

    @IBAction func actionRequested(_ sender: Any) {
        if state == "IDLE" {
            // Send Bluetooth request "GetTargets" to CSM
            print("Frame Requested!")
        
            // Wait for image to be received
        
            // Display image
            frameView.image = UIImage()
        
            // Update system state
            state = "DISPLAYING"
            
        } else if state == "TRACKING" {
            print("hi")
        }
    }
    
    
    
    @IBAction func actionConfirmed(_ sender: Any) {
        // Send target information to CSM for tracking
        
        // Change top button name to "Stop Tracking"
        
        // Update confirm button to Disabled
    }
    
}

