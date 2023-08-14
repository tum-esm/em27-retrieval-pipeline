!     Last change:  BLA   8 Jul 2018    4:09 pm
module globinv10

implicit none

character(len=1),parameter :: pathstr = "/"         ! Windows or Linux
integer,parameter :: n_ifg = 80           ! number of IFG points for modeff calculation
integer,parameter :: n_ilsgrid_ms = 40    ! radius ILS on minimally sampled grid
integer,parameter :: maxspectra = 50000   ! max number of spectra
integer,parameter :: maxnuegrid = 4000000 ! max number of spectral gridpoints
integer,parameter :: maxisagrid = 500000  ! max number of isa gridpoints
integer,parameter :: maxlev = 50
integer,parameter :: maxtau = 10
integer,parameter :: maxjob = 10
integer,parameter :: maxbase = 40
integer,parameter :: maxdww = 20

real(8),parameter :: radtograd = 57.2957795130823d0
real(8),parameter :: gradtorad = 1.74532925199433d-2
real(8),parameter :: pi = 3.141592653589793d0
real(8),parameter :: kwpi = 1.0d0 / 3.141592653589793d0
real(8),parameter :: amu_SI = 1.66053904e-27
real(8),parameter :: semifov_ifm = 2.95d-03
real(8),parameter :: nuechandiv = 5.000d3

character(150) :: datumspfad,abscodatei
character(12),dimension(maxspectra) :: specname
character(50) :: sitename
character(6) :: yymmddchar
logical :: pTdetaildec,refractdec,anyCOdec
integer :: n_spectra,n_tau,n_job,n_Tdisturb,ils_radius,maxpoly,noff_chan1
real :: persist
real(8) :: altim_gnd_ref,pPa_gnd_ref,TKel_gnd_ref


! Datentypen
type instrument
    sequence
    real(8) :: OPDmax
    real(8) :: apolin_inp,apoeff_inp,apophas_inp
    real(8) :: apolin,apoeff,apophas
end type

type invjob
    sequence
    real(8) :: nuel_input,nuer_input
    real(8) :: nuel_mess,nuer_mess
    !real(8) :: nuel_fine,nuer_fine
    integer :: igridl_mess,igridr_mess,ngrid_mess
    integer :: igridl_ref,igridr_ref
    integer :: igridl_isa,igridr_isa
    !integer :: igridl_fine,igridr_fine
    integer,dimension(maxtau) :: method    
    real,dimension(maxtau) :: colskal,colskal_persist
    real,dimension(maxbase) :: baseparm,baseparm_persist
    integer,dimension(maxbase-1) :: base_ptrl,base_ptrr ! pointer on coarse grid
    real :: epsnueskal,epsnueskal_persist
    real :: rms
    !logical :: Tfitdec
    integer :: ngas
    integer :: nderigas
    integer :: nbase
    integer :: niter
    integer :: ndww
    complex(8),dimension(maxdww) :: vw_bnds
    real(8),dimension(maxdww) :: vw_steep
end type

type observer
    sequence
    logical :: COchandec
    integer :: ngrid_mess1,ngrid_mess2
    real(8) :: mea_mess1,mep_mess1
    real(8) :: mea_mess2,mep_mess2
    real(8) :: firstnue_mess1,firstnue_mess2
    real(8) :: dnue_mess1,dnue_mess2
    real(8) :: latrad,lonrad,altim
    real(8) :: JD,sza_rad,azimuth_deg
    real(8) :: mpd1,mpd2
end type

type postprocess
    sequence
    character(len=8), dimension(maxtau) :: Xident
    real,dimension(maxtau) :: AICF,ADCF1,ADCF2
    real,dimension(maxtau) :: col_corr,XVMR
end type

type wvnrskal    ! nue(i) = firstnue * exp((i-1) * dnuerel) note: nue(1/ngrid) = firstnue/lastnue
    sequence
    integer :: ngrid_ref
    integer :: ngrid_isa
    integer :: ngrid_mess
    integer :: ngrid_mess1,ngrid_mess2
    integer :: izf
    integer :: isa
    real(8) :: dnue_ils
    real(8) :: dnue_mess,firstnue_mess,lastnue_mess
    real(8) :: dnuerel,firstnue_ref,lastnue_ref
    real(8),dimension(maxnuegrid) :: nue_ref
    real(8),dimension(maxisagrid) :: nue_isa
end type

type (invjob),dimension(maxjob) :: job
type (postprocess),dimension(maxjob) :: postpro
type (instrument) :: instr
type (observer),dimension(maxspectra) :: obs
type (wvnrskal) wvskal

end module globinv10
