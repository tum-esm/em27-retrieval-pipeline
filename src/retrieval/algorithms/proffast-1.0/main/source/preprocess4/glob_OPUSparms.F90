module glob_OPUSparms

use glob_prepro4,only : maxmeas,maxOPUSchar

implicit none

!    ' RES - resolution
!    ' HFW - high folding limit(should be sligtly less than 15798)
!    ' LWN - laser wavenumber (should be near 15798)
!    ' DAT - date
!    ' TIM - time
!    ' VEL - scanner velocity
!    ' NSS - number of scans (should be even and equal to GFW + GBW)
!    ' GFW - number good fwd scans
!    ' GBW - number of good backward scans
!    ' AQM - acquisition mode (should be DD)
!    ' HPF - high pass filter
!    ' LPF - low pass filter
!    ' TSC - scanner T
!    ' SSM - sample spacing multiplicator (should be 2)  

type OPUS_parameters
    sequence
    character(len=maxOPUSchar) :: DAT ! date
    character(len=maxOPUSchar) :: TIM ! time
    character(len=maxOPUSchar) :: VEL ! scanner velocity ENUM!!
    character(len=maxOPUSchar) :: AQM ! acquisition mode (should be DD)
    character(len=maxOPUSchar) :: HPF ! high pass filter
    character(len=maxOPUSchar) :: LPF ! low pass filter
    integer :: NSS                    ! number of scans (should be even and equal to GFW + GBW)
    integer :: GFW                    ! number good fwd scans
    integer :: GBW                    ! number of good backward scans
    integer :: SSM                    ! sample spacing multiplicator (should be 2)
    real(8) :: RES                    ! resolution
    real(8) :: HFL                    ! high folding limit(should be sligtly less than 15798)
    real(8) :: LWN                    ! laser wavenumber (should be near 15798)
    real(8) :: TSC                    ! scanner T
end type

type (OPUS_parameters) :: OPUS_parms(maxmeas)

end module glob_OPUSparms

