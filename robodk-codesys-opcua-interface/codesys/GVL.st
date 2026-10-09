VAR_GLOBAL

  (* Commands from the visualization / GUI *)

  Trigger : BOOL := FALSE;        // Signal to start the selected program

  Stop : BOOL := FALSE;           // Signal to stop the running program

  Selected_Index : INT := 0;      // Index of the selected program (1..MAX)



  (* Information from Python over OPC UA / feedback from RoboDK *)

  Robot_Run : BOOL := FALSE;      // Status: RoboDK standard program is running

  IO_Run : BOOL := FALSE;         // Status: RoboDK program (Python/standard) is running

  Current_Program : STRING(50) := '';       // Name of the program currently running

  Comb_names : ARRAY[1..50] OF STRING(80);  // List of all available programs

  Nb_Programs : INT := 0;         // Number of programs in the station



  (* Industrial IO - commands PLC -> RoboDK *)

  IO_ : ARRAY[1..50] OF BOOL := [FALSE];    // Control IOs PLC -> RoboDK



  (* Physical start button *)

  Start_IO : BOOL := FALSE;       // Manual start signal for industrial programs

END_VAR
