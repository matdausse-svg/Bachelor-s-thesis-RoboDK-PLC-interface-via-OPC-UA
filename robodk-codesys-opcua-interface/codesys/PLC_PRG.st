PROGRAM PLC_PRG

VAR

  RStart       : R_TRIG;

  RisingStop   : R_TRIG;

  i            : INT;

END_VAR

(* Rising edge detection of the physical start button *)

RStart(CLK := Start_IO);



(* Rising edge detection of the stop button *)

RisingStop(CLK := Stop);



(* ===== STOP ===== *)

IF RisingStop.Q THEN

  Stop := TRUE; (* Latch the stop command *)

END_IF



IF Stop THEN

  (* Immediately reset all IO commands *)

  FOR i := 1 TO 50 DO

    IO_[i] := FALSE;

  END_FOR;

END_IF



(* ===== START ===== *)

IF RStart.Q THEN

  IF (Selected_Index >= 1) AND (Selected_Index <= Nb_Programs) THEN



    (* Reset all IO commands *)

    FOR i := 1 TO 50 DO

      IO_[i] := FALSE;

    END_FOR;



    (* Activate the IO that matches the selected program *)

    IO_[Selected_Index] := TRUE;

  END_IF;



  (* Reset the physical start button *)

  Start_IO := FALSE;

END_IF
