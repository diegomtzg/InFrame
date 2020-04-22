//
//  ViewController.swift
//  InFrame2
//
//  Created by Ike Kilinc on 4/21/20.
//  Copyright © 2020 Ike Kilinc. All rights reserved.
//

import UIKit
import Foundation

class ViewController: UIViewController {
    
    // IDLE, DISPLAYING, TRACKING
    var state = "IDLE"
    
    // Core image filepaths
    let blankImg = "blank_white"
    let loadingImg = "loading_white"
    let testImg = "labeled_test"
    
    @IBOutlet weak var frameView: UIImageView!
    @IBOutlet weak var instructionLabel: UILabel!
    @IBOutlet weak var requestButton: UIButton!
    @IBOutlet weak var bottomButton: UIButton!
    @IBOutlet weak var targetSelection: UILabel!
    @IBOutlet weak var targetSelector: UIStepper!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        // Set background
        self.view.backgroundColor = UIColor(patternImage: UIImage(named: "background")!)
        
        // Set frameView settings and starting image
        frameView.image = UIImage(named: blankImg)
        frameView.layer.masksToBounds = true
        frameView.layer.borderWidth = 3.0
        frameView.layer.borderColor = UIColor.black.cgColor
        frameView.layer.cornerRadius = 5
        
        // Round out buttons
        requestButton.layer.cornerRadius = 10
        bottomButton.layer.cornerRadius = 10
        
        // Set up first instruction
        instructUser(msg: "Request frame to begin target selection")
    }

    @IBAction func actionRequested(_ sender: Any) {
        if state == "IDLE" {
            // Send Bluetooth request "GetTargets" to CSM and display the received frame
            let newFrame = requestFrameViaBluetooth()
            
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                self.frameView.image = UIImage(named: newFrame)
                
                // Enable stepper and label
                self.targetSelection.isEnabled = true
                self.targetSelector.isEnabled = true
                
                // Update user instruction
                self.instructUser(msg: "Scale to target ID and confirm, or request another frame")
            
                // Update system state
                self.state = "DISPLAYING"
            }
            
        } else if state == "DISPLAYING" {
            // Send Bluetooth request "GetTargets" to CSM and display the received frame
            let newFrame = requestFrameViaBluetooth()
            
            
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                self.frameView.image = UIImage(named: newFrame)
                
                // Reset DISPLAYING view
                self.targetSelector.value = 0
                self.targetSelection.text = "No Target"
                self.bottomButton.isEnabled = false
            }
            
        } else if state == "TRACKING" {
            // Reset image display
            frameView.image = UIImage(named: blankImg)
            
            // Reset Action Request button
            requestButton.setTitle("Request Frame", for: UIControl.State.normal)
            
            // Reset target selection
            targetSelection.text = "No Target"
            
            // Update user instruction
            instructUser(msg: "Select 'Stop Recording' to terminate tracking or restart")
            
            state = "IDLE"
            print("Sending 'Stop Recording' to CSM!")
        }
    }
    
    
    
    @IBAction func actionConfirmed(_ sender: Any) {
        // Send target information to CSM for tracking
        
        // Change top button name to "Stop Tracking"
        requestButton.setTitle("Stop Tracking", for: UIControl.State.normal)
        
        // Transition to TRACKING view
        targetSelector.value = 0
        bottomButton.isEnabled = false
        targetSelection.isEnabled = false
        targetSelector.isEnabled = false
        state = "TRACKING"
        
        print("Sending Target Information!")
    }
    
    
    @IBAction func targetSelectionChanged(_ sender: Any) {
        let currVal = Int(round(targetSelector.value))
        // TODO: Check if currVal exists as an Instance value for any detection in currently displayed frame. If not, reset currVal to last valid selection (essentially not allowing switch to invalid selection).
        bottomButton.isEnabled = true
        targetSelection.text = "Target: " + String(currVal)
    }
    
    
    func instructUser(msg: String) {
        instructionLabel.text = msg
    }
    
    func requestFrameViaBluetooth() -> String {
        /*
         Simulates a frame request to the CSM via Bluetooth.
         
         :returns: String - name of frame file saved locally.
         */
        print("Frame Requested!")
        
        // Temporarily display loading image
        frameView.image = UIImage(named: loadingImg)
        
        print("Frame Retrieved!")
        
        return testImg
    }

}

