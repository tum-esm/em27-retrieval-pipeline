!     Last change:  BLA   8 Jul 2018   12:51 pm
module globvar10

implicit none

! Fixed parameters
character(len=1),parameter :: pathstr = "/"         ! Windows or Linux
integer,parameter :: maxlev = 50          ! max number of levels
integer,parameter :: maxams = 5           ! max number of airmasses / raytracing directions
integer,parameter :: maxavk = 15          ! max number of AVK raytracing directions
integer,parameter :: maxpoly = 4          ! number of poly coeffs for approximating sumtau
                                          ! as fct of airmass (only even orders used)
integer,parameter :: maxtau = 10          ! max number of species handled by the forward code at a time
                                          ! (H2O,HDO,CO2,N2O,CO,CH4,O2,HF,HCl)
integer,parameter :: ngridratio = 20      ! ratio between fine and coarse non-equidistant grids
integer,parameter :: maxiso = 10          ! max number of isotopologues of a HITRAN species handeable
integer,parameter :: maxspecies = 150     ! max number of different species wich can be handled
integer,parameter :: maxlines = 500000    ! max number of lines of all species
integer,parameter :: maxnuegrid = 5000000 ! max number of spectral gridpoints
integer,parameter :: iunit_fwd = 10       ! File Handle
! lownue_read = real(firstgrid_mw - gridradius,8) * deltanue_mess
! highnue_read = real(lastgrid_mw + gridradius,8) * deltanue_mess
! lownue_mw = real(firstgrid_mw,8) * deltanue_mess
! highnue_mw = real(lastgrid_mw,8) * deltanue_mess


! Quantities which are set during runtime
! n_lev: Number of model levels
integer :: n_lev,n_tau,n_mw,n_species,ils_radius,n_Tdisturb,nzerofill
character(150),dimension(maxtau) :: hitdatei,vmrdatei
character(150) :: ptdatei,h2odatei,soldatei,specidatei
character(150) :: datumspfad
character(50) :: sitename
character(6) :: yymmddchar
character(50) :: lblkennung,sdgdatei

logical :: pThumdec,filesoutdec
integer,dimension(maxtau) :: iso_handle
integer,dimension(maxiso,maxtau) :: iso_kennung
real(8),dimension(maxtau) :: clipweakline,masseamu_min,totcol

! SI and further constants
real(8),parameter :: pi = 3.141592653589793d0
real(8),parameter :: kwpi = 1.0d0 / 3.141592653589793d0
real(8),parameter :: amunit = 1.6605d-27
real(8),parameter :: kboltz = 1.3807e-23
real(8),parameter :: clicht = 299792458.0d0
real(8),parameter :: Rearth_pol = 6.35675d6
real(8),parameter :: Rearth_equat = 6.37814d6

real(8),parameter :: radtograd = 57.2957795130823d0
real(8),parameter :: gradtorad = 1.74532925199433d-2
real(8),parameter :: mudry = 28.97d0
real(8),parameter :: muh2o = 18.02d0
real(8),parameter :: dgdh = - 3.086d-6 ! grav. accel reduces with altitude (per meter)


type observer
    sequence
    real :: FOVext  ! fractional external FOV
    real(8) :: h_m,lat_rad,lon_rad,p_hPa
    real(8),dimension(maxams) :: sza_gnd_rad ! apparent solar elevation at observer
    real(8),dimension(maxavk) :: sza_gnd_rad_avk ! apparent solar elevation at observer
end type

type speciesinfos
    sequence
    integer :: identifier
    real(8) :: masseamu,qa,qb,qc,qd,qe
end type

type wvnrskal    ! nue(i) = firstnue * exp((i-1) * dnuerel) note: nue(1/ngrid) = firstnue/lastnue
    sequence
    integer :: ngrid
    real(8) :: firstnue_requested,lastnue_requested
    real(8) :: dnuerel,firstnue,lastnue
    real(8) :: nueraytra
    real(8),dimension(maxnuegrid) :: nue
end type

type microwindow
    sequence
    character(len=8) :: gasname
    integer :: istart,istop,nfine,ncoarse
    real(8) :: firstnue_inp,lastnue_inp    
end type


! Allocate types
type (observer) obs
type (speciesinfos) species(maxspecies)
type (wvnrskal) wvskal
type (microwindow) :: mw(maxtau)

end module globvar10
