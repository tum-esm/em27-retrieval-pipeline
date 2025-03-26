! PROFFAST 2 - Retrieval code for the COllaborative Carbon COlumn Network (COCCON)
! Copyright (C)   2022   Frank Hase, Karlsruhe Institut of Technology (KIT)
!
! This program is free software: you can redistribute it and/or modify
! it under the terms of the GNU General Public License version 3 as published by
! the Free Software Foundation.
!
! This program is distributed in the hope that it will be useful,
! but WITHOUT ANY WARRANTY; without even the implied warranty of
! MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
! GNU General Public License for more details.
!
! You should have received a copy of the GNU General Public License
! along with this program.  If not, see <https://www.gnu.org/licenses/>.

!====================================================================
!
! This code has been developed for use with COCCON spectrometers
! by Frank Hase, KIT (frank.hase@kit.edu). It precalculates and
! tabellates daily absorption - xsections to be used by the code "invers"
!
!====================================================================

program pcxs24

use globvar24
use globlev24
use globlin24

implicit none

character(len=300) :: abscodatei,inputdatei,AVKdatei
integer :: i,istart,j,k,ngrid_solspec_inp,next_free_unit
real(8) :: wrkairmass,pfaktor,Tdisturb,pdisturb,firstnue_solspec_inp &
  ,lastnue_solspec_inp,totamp,lorwidth,gauwidth,width

real,dimension(:),allocatable :: solspec_inp,solspec
real,dimension(:),allocatable :: sumtau_zenith,tau_cumula,tau_cumulb
real,dimension(:,:),allocatable :: tau_lev,sumtau
real,dimension(:,:),allocatable :: dtau_dp,dtau_dT
real,dimension(:,:,:),allocatable :: polytau

! general wavenumber abscissa
wvskal%dnuerel = 5.0d-7
wvskal%firstnue_requested = 4150.0d0
wvskal%lastnue_requested = 8500.0d0
wvskal%firstnue = wvskal%firstnue_requested
wvskal%ngrid = nint(log(wvskal%lastnue_requested / wvskal%firstnue) &
  / wvskal%dnuerel) + 1
wvskal%ngrid = nstep * (wvskal%ngrid / nstep) + nstep + 1 ! for common sampling of line wings, note: array element counting starts with index 1
wvskal%lastnue = wvskal%firstnue * exp(real(wvskal%ngrid,8) * wvskal%dnuerel)
wvskal%nueraytra = 0.5d0 * (wvskal%firstnue + wvskal%lastnue)
do i = 1,wvskal%ngrid
    wvskal%nue(i) = wvskal%firstnue * exp(real(i-1,8) * wvskal%dnuerel)
end do
print *,'first wavenumber:        ',wvskal%firstnue
print *,'last wavenumber:         ',wvskal%lastnue
print *,'number of ref grid pts:  ',wvskal%ngrid

! Read general input file (observer coordinates + altitude, pT-file to use)
call get_command_argument(1,inputdatei)
call read_pcxsinput('inp_fast'//pathstr//trim(inputdatei))

! Read incremental level scheme, derive level altitudes
call read_levels('inp_fast'//pathstr//'pcxslev.inp')

! process solar spectrum
call check_solspec(firstnue_solspec_inp,lastnue_solspec_inp,ngrid_solspec_inp)
allocate (solspec_inp(ngrid_solspec_inp),solspec(wvskal%ngrid))
print *,'Reading solar spectrum...         '
call read_solspec(obs%FOVext,ngrid_solspec_inp,solspec_inp)
if (filesoutdec) call tofile_solspec_inp('solspec_inp.dat',firstnue_solspec_inp,lastnue_solspec_inp,ngrid_solspec_inp,solspec_inp)
print *,'Interpolating solar spectrum...   '
call prepare_solspec(firstnue_solspec_inp,lastnue_solspec_inp,ngrid_solspec_inp,solspec_inp,solspec)
print *,'Writing solar spectrum to file... '
if (filesoutdec) call tofile_solspec('solspec.dat',solspec)
deallocate (solspec_inp)

! Read pT file (p(z) and T(z)) either from *.prf or *.mod formatted file
print *,'Reading pT input file...          '
call read_pT(ptdatei,obs%p_hPa,n_lev,lev%h_m(1:n_lev),lev%T_K(1:n_lev) &
  ,lev%p_Pa(1:n_lev),lev%vmr_ppmv(1:n_lev,1),lev%vmr_ppmv(1:n_lev,2))

! Read VMR files (including H2O in position 1, HDO in position 2)
print *,'Reading VMR files...'
if (pThumdec) then
    istart = 3
else
    istart = 1
end if
do i = istart,n_tau
    call read_vmr(vmrdatei(i),i,n_lev,lev%h_m(1:n_lev),lev%vmr_ppmv(1:n_lev,i))
end do

! PCXS is using dry mixing ratios, so transform VMR from wet to dry if input gas profile is specified as wet
! (H2O is in position 1)
if (wetdec(1)) then
    do i = 1,n_lev
        lev%vmr_ppmv(i,1) = lev%vmr_ppmv(i,1) / (1.0d0 - 1.0d-6 * lev%vmr_ppmv(i,1))
    end do
end if
do i = 2,n_tau
    if (wetdec(i)) then
        do j = 1,n_lev
            lev%vmr_ppmv(j,i) = lev%vmr_ppmv(j,i) / (1.0d0 - 1.0d-6 * lev%vmr_ppmv(j,1))    
        end do
    end if
end do

! Write VMR files to file
call tofile_vmr(lev%h_m(1:n_lev),lev%vmr_ppmv(1:n_lev,1:n_tau))

! Generate hydrostatic atmosphere
call hydrostata(obs%lat_rad,lev%h_m(1:n_lev),lev%T_K(1:n_lev),lev%vmr_ppmv(1:n_lev,1) &
  ,lev%p_Pa(1:n_lev),lev%n_cbm(1:n_lev),lev%n_cbm_dry(1:n_lev),lev%colair(1:n_lev) &
  ,lev%colair_do(1:n_lev),lev%colair_up(1:n_lev))

! Write pT profile to file
call tofile_pT(lev%p_Pa(1:n_lev),lev%colair(1:n_lev),lev%T_K(1:n_lev),lev%h_m(1:n_lev) &
,lev%vmr_ppmv(1:n_lev,1),lev%vmr_ppmv(1:n_lev,2))

! calculate total columns
print *,'Calculating total columns...'
do i = 1,n_tau
    totcol(i) = 0.0d0
    do j = n_lev,1,-1
        totcol(i) = totcol(i) + 1.0d-6 * lev%colair(j) * lev%vmr_ppmv(j,i)
    end do
end do

! Raytracing IMPORTANT: airmass direction 1 needs to be equal to 1 (points towards zenith)
do i = 1,maxams
    wrkairmass = 1.0d0 + 0.13d0 * real(i - 1,8) * real(i-1,8)
    obs%sza_gnd_rad(i) = acos(1.0d0 / wrkairmass)
    call raytrace(lev%h_m(1:n_lev),lev%p_Pa(1:n_lev),lev%T_K(1:n_lev),obs%lat_rad &
      ,0.0d0,obs%sza_gnd_rad(i),.true.,lev%sza_rad(1:n_lev,i))
end do

! Definition of directions and raytracing for AVK LOSs
do i = 1,maxavk
    obs%sza_gnd_rad_avk(i) = 85.0d0 * gradtorad * sqrt(real(i - 1,8) / real(maxavk - 1,8))
    call raytrace(lev%h_m(1:n_lev),lev%p_Pa(1:n_lev),lev%T_K(1:n_lev),obs%lat_rad &
      ,0.0d0,obs%sza_gnd_rad_avk(i),.true.,lev%sza_rad_avk(1:n_lev,i))
end do

print *,'raytracing results (airmass ratios):'
do i = 1,n_lev
    !write (*,'(10(ES11.4))') (lev%sza_rad(i,j),j = 1,maxams)
    write (*,'(10(ES11.4))') (cos(obs%sza_gnd_rad(j)) / cos(lev%sza_rad(i,j)),j = 1,maxams)
end do

! Read species info file
call initspecies('inp_fwd'//pathstr//'species-ver2.inf')

! Read SDV table
call initSDV('inp_fwd'//pathstr//'SDVtable.dat')

! estimate strength of neglectable line for each species
do i = 1,n_tau
    totamp = 0.0d0
    do j = 1,n_lev
        lorwidth = 0.05d0 * 9.87167d-6 * lev%p_Pa(j)
        gauwidth = 0.001d0
        width = sqrt(lorwidth * lorwidth + gauwidth * gauwidth)
        totamp = totamp + 1.0d-4 * lev%colair(j) * 1.0d-6 * lev%vmr_ppmv(j,i) / width
    end do
    ! ODmin 1e-3, factor 30 for max slant factor
    clipweakline(i) = 1.0d-3 / (30.0d0 * totamp)
    print *,'Species, line intensity limit: ',i,clipweakline(i)
end do

! Read linelists
call read_hitran_lbl()
if (filesoutdec) call tofile_lblinfos('lblpointer.dat')

! for each species: calculate tau per level for vertical LOS, afterwards total tau for each geometry
allocate (tau_lev(wvskal%ngrid,n_lev))
allocate (sumtau_zenith(wvskal%ngrid),tau_cumula(wvskal%ngrid),tau_cumulb(wvskal%ngrid))
allocate (sumtau(wvskal%ngrid,maxams))
allocate (dtau_dp(wvskal%ngrid,n_tau),dtau_dT(wvskal%ngrid,n_tau))
allocate (polytau(wvskal%ngrid,maxpoly,n_tau))

tau_cumula(:) = 0.0
tau_cumulb(:) = 0.0

do i = 1,n_tau
    print *,'Processing species: ',i

    ! for each species: calculate tau for each level
    do j = 1,n_lev
        print *,'Calculating tau_lev for species and level:',i,j
        call make_tau_lev(lev%p_Pa(j),lev%T_K(j),lev%colair(j),lev%vmr_ppmv(j,i),lev%vmr_ppmv(j,1),i,tau_lev(:,j))
    end do
    
    if (filesoutdec) call tofile_taulev(i,tau_lev)

    ! for each species: calculate total tau for each SZA
    print *,'Calculating total optical thickness ...'
    call make_sumtau(tau_lev,sumtau)
    if (filesoutdec) call tofile_sumtau('sumtau',i,1,sumtau)

    ! for each species: calculate AVKs (approximated)
    print *,'Calculating AVKs ...'
    do k = 1,n_lev
        tau_cumula(:) = tau_cumula(:) + tau_lev(:,k)
    end do
    do k = 1,n_lev
        tau_cumulb(:) = tau_cumulb(:) + tau_lev(:,k) &
          * cos (obs%sza_gnd_rad_avk(maxavk)) / cos(lev%sza_rad_avk(k,maxavk))
    end do
    do j = 1,nsens(i)
        call make_AVK(j,i,tau_lev,tau_cumula,tau_cumulb)
    end do

    ! calculate closed function air mass dependency
    print *,'Calculating closed fct air mass dep...'
    call make_tau_poly(sumtau,polytau(1:wvskal%ngrid,1:maxpoly,i))
    print *,'...closed fct air mass dep calculated!'

    ! derivative section

    ! derivative wrt T (increase T in boundary layer by 5K)
    print *,'Determining dsumtau/dT ...'
    Tdisturb = 5.0d0
    lev%T_K(1:n_Tdisturb) = lev%T_K(1:n_Tdisturb) + Tdisturb
    
    do j = 1,n_Tdisturb
        print *,'Calculating tau_lev for species and level:',i,j
        call make_tau_lev(lev%p_Pa(j),lev%T_K(j),lev%colair(j),lev%vmr_ppmv(j,i),lev%vmr_ppmv(j,1),i,tau_lev(:,j))
    end do

    call make_sumtau_zenith(tau_lev,sumtau_zenith)
    dtau_dT(1:wvskal%ngrid,i) = &
      (sumtau_zenith(1:wvskal%ngrid) - sumtau(1:wvskal%ngrid,1)) / Tdisturb
    if (filesoutdec) call tofile_tau('dtau_dT',i,dtau_dT)

    lev%T_K(1:n_Tdisturb) = lev%T_K(1:n_Tdisturb) - Tdisturb

    ! derivative wrt p, recalculate tau at ground level
    print *,'Determining dsumtau/dp ...'
    pdisturb = 500.0
    pfaktor = (lev%p_Pa(1) + pdisturb) / lev%p_Pa(1)
    lev%p_Pa(1:n_lev) = lev%p_Pa(1:n_lev) * pfaktor

    do j = 1,n_lev
        print *,'Calculating tau_lev for species and level:',i,j
        call make_tau_lev(lev%p_Pa(j),lev%T_K(j),lev%colair(j),lev%vmr_ppmv(j,i),lev%vmr_ppmv(j,1),i,tau_lev(:,j))
    end do

    call make_sumtau_zenith(tau_lev,sumtau_zenith)
    dtau_dp(1:wvskal%ngrid,i) = &
      (sumtau_zenith(1:wvskal%ngrid) - sumtau(1:wvskal%ngrid,1)) / pdisturb
    if (filesoutdec) call tofile_tau('dtau_dp',i,dtau_dp)

    lev%p_Pa(1:n_lev) = lev%p_Pa(1:n_lev) / pfaktor
    !lev%colair(1:n_lev) = lev%colair(1:n_lev) / (1.0d0 + dpfaktor)

end do
print *,'... All species processed!'

! Write column sensitivities to file
print *,'writing column sensitivities to file ...'
AVKdatei = 'out_fast'//pathstr//trim(sitename)//yymmddchar//'-colsens.dat'
call tofile_AVK(trim(AVKdatei))

! Write results in binary file
! gas sumtau,sumtau_dp,sumtau_dT
print *,'generating binary file ...'
abscodatei = 'wrk_fast'//pathstr//trim(sitename)//yymmddchar//'-abscos.bin'
call tobinfile_abscos(trim(abscodatei),lev%p_Pa(1),lev%T_K(1) &
  ,solspec,polytau,dtau_dp,dtau_dT)
print *,'...done!'

print *,'Deallocating arrays ...'
deallocate (polytau)
deallocate (dtau_dp,dtau_dT)
deallocate (tau_lev,sumtau)
deallocate (sumtau_zenith,tau_cumula,tau_cumulb)
deallocate (solspec)
print *,'...deallocated!'
print *,''
print *,'Program pcxs24 finished.'


end program pcxs24
















!====================================================================
!  check_solspec: determine wavenumber bounds and number of points
!                 of input solar spectrum
!====================================================================
subroutine check_solspec(firstnue_solspec_inp,lastnue_solspec_inp,ngrid_solspec_input)

use globvar24, only : soldatei

implicit none

real(8),intent(out) :: firstnue_solspec_inp,lastnue_solspec_inp
integer,intent(out) :: ngrid_solspec_input

integer :: iowert,iunit_fwd,next_free_unit

iunit_fwd = next_free_unit()
open (iunit_fwd,file = soldatei,iostat = iowert,status = 'old',action = 'read')
if (iowert .ne. 0) then
    print *,'Cannot read solar spectrum:'
    print *,soldatei
    stop
end if

call gonext(iunit_fwd,.false.)
read (iunit_fwd,*) firstnue_solspec_inp
read (iunit_fwd,*) lastnue_solspec_inp
read (iunit_fwd,*) ngrid_solspec_input

close (iunit_fwd)

end subroutine check_solspec



!====================================================================
!  gonext: Einlesen bis zum naechsten $ Zeichen
!====================================================================
subroutine gonext(ifile,bindec)

implicit none

integer,intent(in) :: ifile
logical,intent(in) :: bindec

character(1) :: nextchar

nextchar='x'
do while (nextchar /= '$')
    if (bindec) then
        read(ifile) nextchar
    else
        read(ifile,'(A1)') nextchar
    end if
end do

end subroutine gonext



!====================================================================
!  subroutine hydrostat determines pressure from altitude and T
!====================================================================
subroutine hydrostata(lat_obs_rad,h_lev_m,T_lev_K,h2o_lev_ppmv &
  ,p_lev_pa,n_cbm,n_cbm_dry,colair_lev,colair_lev_do,colair_lev_up)

use globvar24

implicit none

real(8),intent(in) :: lat_obs_rad
real(8),dimension(n_lev),intent(in) :: h_lev_m,T_lev_K,h2o_lev_ppmv
real(8),dimension(n_lev),intent(inout) :: p_lev_pa
real(8),dimension(n_lev),intent(out) :: n_cbm,n_cbm_dry,colair_lev &
  ,colair_lev_do,colair_lev_up

integer,parameter :: nfine = 20  ! fine layering for pressure solver
integer :: i,j
real(8) :: g_eff_gnd,g_eff,mutot_amu,mueff_amu,skalh,ptot,h,T,h2o,deltah &
  ,deltaT,deltah2o,sumntot,sumndry,ntot,ndry,ptotmid,slant,wup,wdo,nfracdry &
  ,coldryinlayer
real(8),dimension(n_lev) :: h2o_lev_wrk

! gravitational acceleration as function of altitude
! International Gravity Formula 1967, 1967 Geodetic Reference System,
! Helmert's equation or Clairault's formula
! taken from http://en.wikipedia.org/wiki/Acceleration_due_to_gravity
! (altitude dependent part separated)

! Surface g_eff as function of latitude
g_eff_gnd = 9.780327d0 * (1.0d0 + 0.0053024d0 * sin(lat_obs_rad) * sin(lat_obs_rad) &
      - 5.8d-6 * sin(2.0d0 * lat_obs_rad) * sin(2.0d0 * lat_obs_rad))

! exclude neg H2O VMR
do i = 1,n_lev
    h2o_lev_wrk(i) = h2o_lev_ppmv(i)
    if (h2o_lev_wrk(i) .lt. 0.0d0) then
        print *,'Warning: Neg H2O VMR in hydrostata! Level:',i
        h2o_lev_wrk(i) = 0.0d0
    end if
end do

colair_lev_do(1) = 0.0d0
do i = 1,n_lev - 1

    ptot = p_lev_pa(i) ! init pressure at bottom of first sublayers

    deltah = (h_lev_m(i+1) - h_lev_m(i)) / real(nfine,8)
    deltaT = (T_lev_K(i+1) - T_lev_K(i)) / real(nfine,8)
    deltah2o = (h2o_lev_wrk(i+1) - h2o_lev_wrk(i)) / real(nfine,8)

    ! determine pressure stratification
    sumntot = 0.0d0
    sumndry = 0.0d0
    mueff_amu = 0.0d0
    wup = 0.0d0
    wdo = 0.0d0
    do j = 1,nfine
        ! determine prescribed and derived values in the middle of sublayer
        h = h_lev_m(i) + (real(j,8) - 0.5d0) * deltah
        T = T_lev_K(i) + (real(j,8) - 0.5d0) * deltaT
        g_eff = g_eff_gnd + dgdh * h
        h2o = h2o_lev_wrk(i) + (real(j,8) - 0.5d0) * deltah2o
        mutot_amu = (mudry + 1.0d-6 * h2o * muh2o) / (1.0d0 + 1.0d-6 * h2o)
        skalh = kboltz * T / (g_eff * mutot_amu * amunit)
        ptotmid = ptot * exp(-0.5d0 * deltah / skalh) ! pressure in middle of sublayer
        ! determine pressure at top of current sublayer
        ptot = ptot * exp(-deltah / skalh)

        ! determine number-density-weighted means
        ntot = ptotmid / (kboltz * T) ! mean total number density in layer
        ndry = ntot / (1.0d0 + 1.0d-6 * h2o)
        sumntot = sumntot + ntot
        sumndry = sumndry + ndry
        mueff_amu = mueff_amu + mutot_amu * ntot
        slant = (real(j,8) - 0.5d0) / real(nfine,8)
        wup = wup + ndry * (1.0d0 - slant)
        wdo = wdo + ndry * (slant)
    end do
    p_lev_pa(i+1) = ptot
    mueff_amu = mueff_amu / sumntot
    nfracdry = sumndry / sumntot
    wup = wup / sumndry
    wdo = wdo / sumndry

    ! determine partial columns *associated with each level*
    ! col_do,col_up,col = col_do + col_up
    coldryinlayer = nfracdry * (p_lev_pa(i) - p_lev_pa(i+1)) &
      / (mueff_amu * amunit * (g_eff_gnd + 0.5d0 * dgdh * (h_lev_m(i+1) + h_lev_m(i))))

    colair_lev_do(i+1) = coldryinlayer * wdo / (wup + wdo)
    colair_lev_up(i) = coldryinlayer * wup / (wup + wdo)
    colair_lev(i) = colair_lev_do(i) + colair_lev_up(i)
end do

colair_lev(n_lev) = colair_lev_do(n_lev)
colair_lev_up(n_lev) = 0.0d0

! Determine total and dry particle number density at each level
do i = 1,n_lev
    n_cbm(i) = p_lev_pa(i) / (kboltz * T_lev_K(i))
    n_cbm_dry(i) = p_lev_pa(i) / ((1.0d0 + 1.0d-6 * h2o_lev_wrk(i)) * kboltz * T_lev_K(i))
end do

print *,'pT profile after hydrostat rebalancing:'
do i = 1,n_lev
    write (*,'(5(ES11.4))') h_lev_m(i),T_lev_K(i),p_lev_Pa(i),n_cbm(i),n_cbm_dry(i)
end do


end subroutine hydrostata



!====================================================================
!  infospecies
!====================================================================
subroutine infospecies(whichspecies,masseamu,qa,qb,qc,qd,qe,qf,qg)

use globvar24

implicit none
integer,intent(in) :: whichspecies
real(8),intent(out) :: masseamu,qa,qb,qc,qd,qe,qf,qg

logical :: decmarke
integer :: i

decmarke = .false.
do i = 1,n_species
    if (whichspecies .eq. species(i)%identifier) then
        masseamu = species(i)%masseamu
        qa = species(i)%qa
        qb = species(i)%qb
        qc = species(i)%qc
        qd = species(i)%qd
        qe = species(i)%qe
        qf = species(i)%qf
        qg = species(i)%qg
        decmarke = .true.
    end if
end do

if (.not. decmarke) then
    print *,'Requested species: ',whichspecies
    call warnout('Error in infospecies: no species assignment!',0)
end if

end subroutine infospecies


!====================================================================
!  initspecies: Initialize masses and Gamache coeffs
!====================================================================
subroutine initSDV(SDVdatei)

use globlin24

implicit none

character(len=*),intent(in) :: SDVdatei
integer :: i,j,iowert,iunit_fwd,next_free_unit
real :: realdum

iunit_fwd = next_free_unit()
open (iunit_fwd,file = SDVdatei,status = 'old',action = 'read',iostat = iowert)
if (iowert .ne. 0) then
    print *,SDVdatei
    call warnout('Cannot open SDV lookup table!',0)
end if
call gonext(iunit_fwd,.false.)

do i = -nSDV,nSDV
    read (iunit_fwd,*) realdum,realdum,realdum,realdum,(SDVtab(j,i),j = 1,7)
end do
close (iunit_fwd)

end subroutine initSDV



!====================================================================
!  initspecies: Initialize masses and Gamache coeffs
!====================================================================
subroutine initspecies(speciesdatei)

use globvar24
use globlev24

implicit none

character(len=*),intent(in) :: speciesdatei
integer :: i,iowert,iunit_fwd,next_free_unit
real :: realdum

i = 0
iunit_fwd = next_free_unit()
open (iunit_fwd,file = speciesdatei,status = 'old',action = 'read',iostat = iowert)
if (iowert .ne. 0) then
    print *,speciesdatei
    call warnout('Cannot open species file!',0)
end if
call gonext(iunit_fwd,.false.)
do
    i = i + 1
    if (i .gt. maxspecies) then
        print *,'Maximum possible number of species is:',maxspecies
        call warnout('Error in initspecies: Too many Species!  ',0)
    end if
    read (iunit_fwd,*,end = 100) species(i)%identifier,species(i)%masseamu &
      ,realdum,species(i)%qa,species(i)%qb,species(i)%qc,species(i)%qd &
      ,species(i)%qe,species(i)%qf,species(i)%qg
    ! Teste Speciesmasse
    if (species(i)%masseamu .lt. 0.99d0) then
        print *,species(i)%identifier,species(i)%masseamu
        call warnout("species mass < 1 amu!",0)
    end if
    if (species(i)%masseamu .gt. 1.0d3) then
        print *,species(i)%identifier,species(i)%masseamu
        call warnout("species mass > 1000 amu!",0)
    end if
end do
100 continue
close (iunit_fwd)
n_species = i

end subroutine initspecies



!====================================================================
!  subroutine make_AVK: estimation of column sensitivities
!====================================================================
subroutine make_AVK(isens,igas,tau_lev,tau_cumula,tau_cumulb)

use globvar24
use globlev24

implicit none

integer,intent(in) :: isens,igas
real,dimension(wvskal%ngrid,n_lev),intent(in) :: tau_lev
real,dimension(wvskal%ngrid),intent(in) :: tau_cumula,tau_cumulb

integer :: i,j,ic,jf,kf,ilsradius,istart,istop
real :: weight
real(8) :: dnue,norm,ratio,wert,ata,atb
real,dimension(:),allocatable :: tau,trm,wrkfa,wrkfb,ILS,wrka,wrkb

! determine spectral grid width in MW
dnue = (0.5d0 * (mw(isens,igas)%firstnue_inp + mw(isens,igas)%lastnue_inp)) * wvskal%dnuerel

! initialize normalized ILS
ilsradius = 1.0d0 / dnue
allocate (ILS(-ilsradius:ilsradius))
norm = 0.0d0
do i = -ilsradius,ilsradius
    wert = 3.636d0 * dnue * real(i,8)
    ILS(i) = exp(-wert * wert)
    norm = norm + ILS(i)
end do
ILS(:) = ILS(:) / norm

! allocate further arrays
allocate (tau(1-ilsradius:mw(isens,igas)%nfine+ilsradius),trm(1-ilsradius:mw(isens,igas)%nfine+ilsradius))
allocate (wrkfa(1-ilsradius:mw(isens,igas)%nfine+ilsradius),wrkfb(1-ilsradius:mw(isens,igas)%nfine+ilsradius))
allocate (wrka(1:mw(isens,igas)%ncoarse),wrkb(1:mw(isens,igas)%ncoarse))

istart = mw(isens,igas)%istart-ilsradius
istop = mw(isens,igas)%istop+ilsradius

do i = 1,maxavk
    ! calculate tau
    tau(:) = 0.0
    do j = 1,n_lev
        tau(1-ilsradius:mw(isens,igas)%nfine+ilsradius) = tau(1-ilsradius:mw(isens,igas)%nfine+ilsradius) &
          + tau_lev(istart:istop,j) / cos(lev%sza_rad_avk(j,i))
    end do

    ! calculate trm (interpolation between tau_cumula and tau_cumulb - linear in airmass)
    weight = real((1.0d0 / cos(obs%sza_gnd_rad_avk(i)) - 1.0d0) &
      / (1.0d0 / cos(obs%sza_gnd_rad_avk(maxavk)) - 1.0d0))
    trm(1-ilsradius:mw(isens,igas)%nfine+ilsradius) = &
      exp(-((1.0 - weight) * tau_cumula(istart:istop) + weight * tau_cumulb(istart:istop)) &
      / cos(obs%sza_gnd_rad_avk(i)))

    ! wrkfa = - trm * tau
    wrkfa(:) = - trm(:) * tau(:)

    ! convolution of wrkfa with ILS, resampling
    ic = 1
    do jf = 1,mw(isens,igas)%nfine,ngridratio 
        wert = 0.0d0
        do kf = -ilsradius,ilsradius
            wert = wert + wrkfa(jf-kf) * ILS(kf)
        end do
        wrka(ic) = wert
        ic = ic + 1
    end do
    ata = dot_product(wrka,wrka)

    do j = 1,n_lev
        ! wrkfb = totcol / col_in_lev * trm * taulev
        ratio = totcol(igas) / (1.0e-6 * lev%colair(j) * lev%vmr_ppmv(j,igas))
        wrkfb(:) = - ratio * trm(:) * tau_lev(istart:istop,j) / cos(lev%sza_rad_avk(j,i))

        ! convolution of wrkb with ILS
        ic = 1
        do jf = 1,mw(isens,igas)%nfine,ngridratio 
            wert = 0.0d0
            do kf = -ilsradius,ilsradius
                wert = wert + wrkfb(jf-kf) * ILS(kf)
            end do
            wrkb(ic) = wert
            ic = ic + 1
        end do

        ! column sensitivity is (wrkaT * wrka)-1 * (wrkaT * wrkb)
        atb = dot_product(wrka,wrkb)
        lev%colsens(j,i,isens,igas) = atb / ata
    end do

end do

deallocate (ILS)
deallocate (wrka,wrkb)
deallocate (wrkfa,wrkfb)
deallocate (tau,trm)

end subroutine make_AVK



!====================================================================
!  subroutine make_sumtau: calculates total optical thickness for selected SZAs
!====================================================================
subroutine make_sumtau (tau_lev,sumtau)

use globvar24
use globlev24

implicit none

real,dimension(wvskal%ngrid,n_lev),intent(in) :: tau_lev
real,dimension(wvskal%ngrid,maxams),intent(inout) :: sumtau

integer  :: j,k
real  :: amsfaktor

sumtau = 0.0

do j = 1,maxams
    do k = 1,n_lev
        !amsfaktor = 1.0 / cos(lev%sza_rad(k,j))
        amsfaktor = cos(obs%sza_gnd_rad(j)) / cos(lev%sza_rad(k,j))
        sumtau(:,j) = sumtau(:,j) + tau_lev(:,k) * amsfaktor
    end do
end do

end subroutine make_sumtau



!====================================================================
!  subroutine make_sumtau_zenith: calculates total optical thickness for zenith
!====================================================================
subroutine make_sumtau_zenith (tau_lev,sumtau_zenith)

use globvar24
use globlev24

implicit none

real,dimension(wvskal%ngrid,n_lev),intent(in) :: tau_lev
real,dimension(wvskal%ngrid),intent(out) :: sumtau_zenith

integer  :: j,k
real  :: amsfaktor

sumtau_zenith = 0.0

do k = 1,n_lev
    sumtau_zenith(:) = sumtau_zenith(:) + tau_lev(:,k)
end do

end subroutine make_sumtau_zenith



!====================================================================
!  subroutine make_tau_lev: calculates zenith optical depth for selected level and species
!====================================================================
subroutine make_tau_lev(p_Pa,T_K,colair,vmr_ppmv,vmrh2o_ppmv,itau,tau_lev)

use globvar24
use globlin24

implicit none

real(8),intent(in) :: p_Pa,T_K,colair,vmr_ppmv,vmrh2o_ppmv
integer,intent(in) :: itau
real,dimension(wvskal%ngrid),intent(inout) :: tau_lev

integer :: k,l,igridfirst,igridlast,igridfirstin,igridlastin,icenter,ix,ngauradius
real :: xwert,ya,yb,yc,yd,ycminyb,slopel,sloper,spkwnenner
real(8) :: reslinenue,voigtnorm,lorhwhm,lorhwhmqu,lorhwhm_limit,bgau,gauhwhm,gauhwhmqu,gascol &
  ,make_vnorm,deltanue,deltanuequ,lowdeltanue,highdeltanue,ratio,rkern,rkernin,normfaktor,sockel &
  ,LMTwert,LMY,voigthwhm,voigthwhmqu,voigthwhminv,LMsockel,LMfaktor,x,gam2ratio,amp,ampexpo &
  ,relnue,relnuequ,SDVsockel,SDVwert,lorwert,kwnenner,LMwert,faltung,sumgau,korrwing

logical,dimension(:),allocatable :: signaldec,convdec
real,dimension(:),allocatable :: wrktaua,wrktaub,gausskernel

allocate (wrktaua(wvskal%ngrid),wrktaub(wvskal%ngrid))
allocate (signaldec(wvskal%ngrid),convdec(wvskal%ngrid))

rkern = 25.0d0
rkernin = 0.5d0

tau_lev(1:wvskal%ngrid) = 0.0
wrktaua(1:wvskal%ngrid) = 0.0
wrktaub(1:wvskal%ngrid) = 0.0
signaldec(1:wvskal%ngrid) = .false.
convdec(1:wvskal%ngrid) = .false.

gascol = 1.0e-6 * colair * vmr_ppmv

bgau = wvskal%firstnue / clicht * sqrt(2.0d0 * kboltz * T_K / (amunit * masseamu_min(itau)))
ngauradius = int(5.0d0 * bgau / (wvskal%firstnue * wvskal%dnuerel))

do k = lines%lb(itau),lines%rb(itau)
    reslinenue = lines%nue(k) + 9.87167d-6 * p_Pa * lines%pshift(k)
    voigtnorm = kwpi * gascol * make_vnorm(lines%species(k),lines%nue(k),lines%ergniveau(k),lines%kappacm(k),T_K)
    gauhwhm = 0.83255461d0 * bgau * reslinenue / wvskal%firstnue
    gauhwhmqu = gauhwhm * gauhwhm
    korrwing = 2.5d0 * gauhwhmqu
    lorhwhm = 9.87167d-6 * p_Pa * ((1.0d0 - 1.0d-6 * vmrh2o_ppmv) * lines%lorwidthf(k) &
      + 1.0d-6 * vmrh2o_ppmv * lines%lorwidths(k)) * (296.0d0 / T_K)**lines%lortdepend(k)

    igridfirst = nint(log((reslinenue - rkern) / wvskal%firstnue) / wvskal%dnuerel) + 1
    igridlast = nint(log((reslinenue + rkern) / wvskal%firstnue) / wvskal%dnuerel) + 1
    igridfirstin = nint(log((reslinenue - rkernin) / wvskal%firstnue) / wvskal%dnuerel) + 1
    igridlastin = nint(log((reslinenue + rkernin) / wvskal%firstnue) / wvskal%dnuerel) + 1
    icenter = nint(log(reslinenue / wvskal%firstnue) / wvskal%dnuerel) + 1

    ! adjust boarders to reside on coarse grid
    do while (mod(igridfirst - 1,nstep) .ne. 0)
        igridfirst = igridfirst + 1
    end do
    do while (mod(igridlast - 1,nstep) .ne. 0)
        igridlast = igridlast - 1
    end do
    do while (mod(igridfirstin - 1,nstep) .ne. 0)
        igridfirstin = igridfirstin - 1
    end do
    do while (mod(igridlastin - 1,nstep) .ne. 0)
        igridlastin = igridlastin + 1
    end do

    normfaktor = voigtnorm * lorhwhm
    lorhwhmqu = lorhwhm * lorhwhm
    sockel = normfaktor / (lorhwhmqu + rkern * rkern)
    lorhwhm_limit = reslinenue * wvskal%dnuerel 

    ! Lorentzlinie berechnen
    ! Innenbereich
    ! igridfirstin - 1
    deltanuequ = (wvskal%nue(igridfirstin - 1) - reslinenue) * (wvskal%nue(igridfirstin - 1) - reslinenue)
    ya = normfaktor / (lorhwhmqu + deltanuequ) - sockel
    ! igridfirstin
    deltanuequ = (wvskal%nue(igridfirstin) - reslinenue) * (wvskal%nue(igridfirstin) - reslinenue)
    yb = normfaktor / (lorhwhmqu + deltanuequ) - sockel
    if (lorhwhm .lt. lorhwhm_limit) then
        ! linke Flanke Innenbereich
        do l = igridfirstin + 1,icenter - 2
            deltanuequ = (wvskal%nue(l) - reslinenue) * (wvskal%nue(l) - reslinenue)
            lorwert = normfaktor / (lorhwhmqu + deltanuequ) - sockel
            wrktaua(l) = wrktaua(l) + lorwert
        end do
        lowdeltanue = wvskal%firstnue * exp(real(icenter - 2,8) * wvskal%dnuerel) - reslinenue
        highdeltanue = wvskal%firstnue * exp(real(icenter,8) * wvskal%dnuerel) - reslinenue
        ratio = (atan(highdeltanue / lorhwhm) - atan(lowdeltanue / lorhwhm)) &
          / (atan(highdeltanue / lorhwhm_limit) - atan(lowdeltanue / lorhwhm_limit))
          ratio = 0.66d0 * (ratio - 1.0d0) + 1.0d0
        ! Drei Punkte um Linienzentrum
        do l = icenter - 1,icenter + 1
            deltanuequ = (wvskal%nue(l) - reslinenue) * (wvskal%nue(l) - reslinenue) 
            lorwert =  ratio * voigtnorm * lorhwhm_limit / (lorhwhm_limit * lorhwhm_limit + deltanuequ) - sockel
            wrktaua(l) = wrktaua(l) + lorwert
        end do
        ! rechte Flanke Innenbereich
        do l = icenter + 2,igridlastin - 1
            deltanuequ = (wvskal%nue(l) - reslinenue) * (wvskal%nue(l) - reslinenue)
            lorwert = normfaktor / (lorhwhmqu + deltanuequ) - sockel
            wrktaua(l) = wrktaua(l) + lorwert
        end do        
    else
        ! gesamter Innenbereich
        do l = igridfirstin + 1,igridlastin - 1
            deltanuequ = (wvskal%nue(l) - reslinenue) * (wvskal%nue(l) - reslinenue)
            lorwert = normfaktor / (lorhwhmqu + deltanuequ) - sockel
            wrktaua(l) = wrktaua(l) + lorwert
        end do
    end if
    ! igridlastin
    deltanuequ = (wvskal%nue(igridlastin) - reslinenue) * (wvskal%nue(igridlastin) - reslinenue)
    yc = normfaktor / (lorhwhmqu + deltanuequ) - sockel
    ! igridlastin + 1
    deltanuequ = (wvskal%nue(igridlastin + 1) - reslinenue) * (wvskal%nue(igridlastin + 1) - reslinenue)
    yd = normfaktor / (lorhwhmqu + deltanuequ) - sockel
    ! linke Flanke jenseits Innenbereich bis Rand, grobe Aufloesung, Korrektur fuer ausgelassene Faltung
    do l = igridfirstin,igridfirst,-nstep
        kwnenner = 1.0d0 / (lorhwhmqu + (wvskal%nue(l) - reslinenue) * (wvskal%nue(l) - reslinenue))
        lorwert = normfaktor * (1.0d0 + korrwing * kwnenner) * kwnenner - sockel
        tau_lev(l) = tau_lev(l) + lorwert
        signaldec(l) = .true.
    end do
    signaldec(igridfirst - nstep) = .true.
    convdec(igridfirstin - ngauradius:igridlastin + ngauradius) = .true.
    ! rechte Flanke jenseits Innenbereich bis Rand, grobe Aufloesung, Korrektur fuer ausgelassene Faltung
    do l = igridlastin,igridlast,nstep
        kwnenner = 1.0d0 / (lorhwhmqu + (wvskal%nue(l) - reslinenue) * (wvskal%nue(l) - reslinenue))
        lorwert = normfaktor * (1.0d0 + korrwing * kwnenner) * kwnenner - sockel
        tau_lev(l) = tau_lev(l) + lorwert
        signaldec(l) = .true.
    end do
    signaldec(igridlast + nstep) = .true.
    ! Polynom Innenbereich subtrahieren
    slopel = (yb - ya) * real((wvskal%nue(igridlastin) - wvskal%nue(igridfirstin)) &
      / (wvskal%nue(igridfirstin) - wvskal%nue(igridfirstin - 1)))
    sloper = (yd - yc) * real((wvskal%nue(igridlastin) - wvskal%nue(igridfirstin)) &
      / (wvskal%nue(igridlastin + 1) - wvskal%nue(igridlastin)))
    ycminyb = yc - yb
    kwnenner = 1.0d0 / (wvskal%nue(igridlastin) - wvskal%nue(igridfirstin))
    do l = igridfirstin + 1, igridlastin - 1
        xwert = (wvskal%nue(l) - wvskal%nue(igridfirstin)) * kwnenner
        wrktaua(l) = wrktaua(l) - (yb + xwert * (slopel + xwert * &
              (3.0 * ycminyb - 2.0 * slopel - sloper + xwert * (-2.0 * ycminyb + slopel + sloper))))
    end do
    ! Polynom Innenbereich addieren (grobe Aufloesung)
    do l = igridfirstin + nstep, igridlastin - nstep, nstep
        xwert = (wvskal%nue(l) - wvskal%nue(igridfirstin)) * kwnenner
        tau_lev(l) = tau_lev(l) + yb + xwert * (slopel + xwert * &
              (3.0 * ycminyb - 2.0 * slopel - sloper + xwert * (-2.0 * ycminyb + slopel + sloper)))
        signaldec(l) = .true.
    end do

    ! line mixing  (not to be convolved with Doppler core)
    if (lines%LMdec(k)) then
        LMTwert = 0.01666667d0 * (T_K - 260.0d0) ! LM-Ref Temperaturen: 200/260/320 K
        LMY = 9.871668d-6 * p_Pa * (lines%LMY(k) + LMTwert * (lines%LMTK1(k) + LMTwert * lines%LMTK2(k)))
        voigthwhm = 0.5346 * lorhwhm + sqrt(0.2166 * lorhwhmqu + gauhwhmqu)
        voigthwhmqu = voigthwhm * voigthwhm
        voigthwhminv = 1.0d0 / voigthwhm
        LMfaktor = LMY * voigtnorm * lorhwhm * voigthwhminv
        LMsockel = LMfaktor / (voigthwhmqu + rkern * rkern) 
        ! Innenbereich
        ! igridfirstin - 1
        deltanue = wvskal%nue(igridfirstin - 1) - reslinenue
        ya = deltanue * (LMfaktor / (voigthwhmqu + deltanue * deltanue) - LMsockel)
        ! igridfirstin
        deltanue = wvskal%nue(igridfirstin) - reslinenue
        yb = deltanue * (LMfaktor / (voigthwhmqu + deltanue * deltanue) - LMsockel)
        do l = igridfirstin + 1,igridlastin - 1
            deltanue = (wvskal%nue(l) - reslinenue)
            LMwert = deltanue * (LMfaktor / (voigthwhmqu + deltanue * deltanue) - LMsockel)
            wrktaub(l) = wrktaub(l) + LMwert
        end do
        ! igridlastin
        deltanue = wvskal%nue(igridlastin) - reslinenue
        yc = deltanue * (LMfaktor / (voigthwhmqu + deltanue * deltanue) - LMsockel)
        ! igridlastin + 1
        deltanue = wvskal%nue(igridlastin + 1) - reslinenue
        yd = deltanue * (LMfaktor / (voigthwhmqu + deltanue * deltanue) - LMsockel)

        ! linke Flanke jenseits Innenbereich bis Rand, grobe Aufloesung
        do l = igridfirstin,igridfirst,-nstep
            deltanue = (wvskal%nue(l) - reslinenue)
            LMwert = deltanue * (LMfaktor / (voigthwhmqu + deltanue * deltanue) - LMsockel)
            tau_lev(l) = tau_lev(l) + LMwert
        end do
        ! rechte Flanke jenseits Innenbereich bis Rand, grobe Aufloesung
        do l = igridlastin,igridlast,nstep
            deltanue = (wvskal%nue(l) - reslinenue)
            LMwert = deltanue * (LMfaktor / (voigthwhmqu + deltanue * deltanue) - LMsockel)
            tau_lev(l) = tau_lev(l) + LMwert
        end do
    else
        ya = 0.0
        yb = 0.0
        yc = 0.0
        yd = 0.0  
    end if

    ! additive SDV correction (not to be convolved with Doppler core)
    if (lines%SDVdec(k)) then
        gam2ratio = lines%gam2ratio(k) * (296.0d0 / T_K)**lines%gam2tdep(k) / (296.0d0 / T_K)**lines%lortdepend(k) 
        if (gam2ratio .gt. 0.2d0) gam2ratio = 0.2d0
        x = (lorhwhm - gauhwhm) / (lorhwhm + gauhwhm)
        voigthwhm = 0.5346 * lorhwhm + sqrt(0.2166 * lorhwhmqu + gauhwhmqu)
        voigthwhminv = 1.0d0 / voigthwhm
            
        ! amplitude as fct of d for reference gam2/gam0 = 0.1
        if (x .lt. 0.0d0) then ! -1 <= d < 0.0
            amp = 0.01185d0 + x * (-0.00299d0 + x * (-0.01935d0 - x * 0.0045d0))
        else ! 0.0 <= x <= 1.0
            if (x .lt. 0.50d0) then
                amp = 0.01185d0 + x * (-0.0025d0 + x * (-0.01978d0 + x * 0.01382d0))
            else
                amp = 0.00958d0 + x * (0.01421d0 + x * (-0.06493d0 + x * (0.06557d0 - x * 0.02028d0)))
            end if
        end if
        amp = pi * voigtnorm * voigthwhminv * amp

        ! scaling behaviour in gam2/gam0 as fct of d (reference gam2/gam0 = 0.1)
        if (x .lt. 0.0d0) then
            ampexpo = 1.11335d0 + x * (0.15351d0 + x * (0.12099d0 + x * (0.14074d0 + x * 0.05809d0)))
        else
            ampexpo = 1.1134d0 &
              + x * (0.1328d0 + x * (0.8374d0 + x * (-3.1487d0 + x * (10.91704d0 + x * (-11.71141 + x * 3.76665d0)))))
        end if
        amp = amp * (10.0d0 * gam2ratio) ** ampexpo     

        relnue = rkern * voigthwhminv
        relnuequ = relnue * relnue
        ix = nint(20.2d0 * x) ! nearest SDV table line is nint(x / 0.99 * 20)
        SDVsockel = (1.0d0 + relnuequ * (SDVtab(1,ix) + relnuequ * SDVtab(2,ix))) &
          / (1.0d0 + relnuequ * (SDVtab(3,ix) + relnuequ * (SDVtab(4,ix) + relnuequ * &
          (SDVtab(5,ix) + relnuequ * (SDVtab(6,ix) + relnuequ * SDVtab(7,ix))))))

        ! Innenbereich
        ! igrdidfirstin - 1
        relnue = (wvskal%nue(igridfirstin - 1) - reslinenue) * voigthwhminv
        relnuequ = relnue * relnue
        SDVwert = amp * ((1.0d0 + relnuequ * (SDVtab(1,ix) + relnuequ * SDVtab(2,ix))) &
          / (1.0d0 + relnuequ * (SDVtab(3,ix) + relnuequ * (SDVtab(4,ix) + relnuequ * &
          (SDVtab(5,ix) + relnuequ * (SDVtab(6,ix) + relnuequ * SDVtab(7,ix)))))) - SDVsockel)
        ya = ya + SDVwert
        ! igridfirstin
        relnue = (wvskal%nue(igridfirstin) - reslinenue) * voigthwhminv
        relnuequ = relnue * relnue
        SDVwert = amp * ((1.0d0 + relnuequ * (SDVtab(1,ix) + relnuequ * SDVtab(2,ix))) &
          / (1.0d0 + relnuequ * (SDVtab(3,ix) + relnuequ * (SDVtab(4,ix) + relnuequ * &
          (SDVtab(5,ix) + relnuequ * (SDVtab(6,ix) + relnuequ * SDVtab(7,ix)))))) - SDVsockel)
        yb = yb + SDVwert
        do l = igridfirstin + 1,igridlastin - 1
            relnue = (wvskal%nue(l) - reslinenue) * voigthwhminv
            relnuequ = relnue * relnue
            SDVwert = amp * ((1.0d0 + relnuequ * (SDVtab(1,ix) + relnuequ * SDVtab(2,ix))) &
              / (1.0d0 + relnuequ * (SDVtab(3,ix) + relnuequ * (SDVtab(4,ix) + relnuequ * &
              (SDVtab(5,ix) + relnuequ * (SDVtab(6,ix) + relnuequ * SDVtab(7,ix)))))) - SDVsockel)
            wrktaub(l) = wrktaub(l) + SDVwert
        end do
        ! igridlastin
        relnue = (wvskal%nue(igridlastin) - reslinenue) * voigthwhminv
        relnuequ = relnue * relnue
        SDVwert = amp * ((1.0d0 + relnuequ * (SDVtab(1,ix) + relnuequ * SDVtab(2,ix))) &
          / (1.0d0 + relnuequ * (SDVtab(3,ix) + relnuequ * (SDVtab(4,ix) + relnuequ * &
          (SDVtab(5,ix) + relnuequ * (SDVtab(6,ix) + relnuequ * SDVtab(7,ix)))))) - SDVsockel)
        yc = yc + SDVwert
        ! igridlastin + 1
        relnue = (wvskal%nue(igridlastin + 1) - reslinenue) * voigthwhminv
        relnuequ = relnue * relnue
        SDVwert = amp * ((1.0d0 + relnuequ * (SDVtab(1,ix) + relnuequ * SDVtab(2,ix))) &
          / (1.0d0 + relnuequ * (SDVtab(3,ix) + relnuequ * (SDVtab(4,ix) + relnuequ * &
          (SDVtab(5,ix) + relnuequ * (SDVtab(6,ix) + relnuequ * SDVtab(7,ix)))))) - SDVsockel)
        yd = yd + SDVwert
        ! linke Flanke jenseits Innenbereich bis Rand, grobe Aufloesung
        do l = igridfirstin,igridfirst,-nstep
            relnue = (wvskal%nue(l) - reslinenue) * voigthwhminv
            relnuequ = relnue * relnue
            SDVwert = amp * ((1.0d0 + relnuequ * (SDVtab(1,ix) + relnuequ * SDVtab(2,ix))) &
              / (1.0d0 + relnuequ * (SDVtab(3,ix) + relnuequ * (SDVtab(4,ix) + relnuequ * &
              (SDVtab(5,ix) + relnuequ * (SDVtab(6,ix) + relnuequ * SDVtab(7,ix)))))) - SDVsockel)
            tau_lev(l) = tau_lev(l) + SDVwert
        end do
        ! rechte Flanke jenseits Innenbereich bis Rand, grobe Aufloesung
        do l = igridlastin,igridlast,nstep
            relnue = (wvskal%nue(l) - reslinenue) * voigthwhminv
            relnuequ = relnue * relnue
            SDVwert = amp * ((1.0d0 + relnuequ * (SDVtab(1,ix) + relnuequ * SDVtab(2,ix))) &
              / (1.0d0 + relnuequ * (SDVtab(3,ix) + relnuequ * (SDVtab(4,ix) + relnuequ * &
              (SDVtab(5,ix) + relnuequ * (SDVtab(6,ix) + relnuequ * SDVtab(7,ix)))))) - SDVsockel)
            tau_lev(l) = tau_lev(l) + SDVwert
        end do
    end if

    if (lines%LMdec(k) .or. lines%SDVdec(k)) then
        ! Polynom Innenbereich subtrahieren
        slopel = (yb - ya) * real((wvskal%nue(igridlastin) - wvskal%nue(igridfirstin)) &
          / (wvskal%nue(igridfirstin) - wvskal%nue(igridfirstin - 1)))
        sloper = (yd - yc) * real((wvskal%nue(igridlastin) - wvskal%nue(igridfirstin)) &
          / (wvskal%nue(igridlastin + 1) - wvskal%nue(igridlastin)))
        ycminyb = yc - yb
        kwnenner = 1.0d0 / (wvskal%nue(igridlastin) - wvskal%nue(igridfirstin))
        do l = igridfirstin + 1, igridlastin - 1
            xwert = (wvskal%nue(l) - wvskal%nue(igridfirstin)) * kwnenner
            wrktaub(l) = wrktaub(l) - (yb + xwert * (slopel + xwert * &
              (3.0 * ycminyb - 2.0 * slopel - sloper + xwert * (-2.0 * ycminyb + slopel + sloper))))
        end do
        ! Polynom Innenbereich addieren (grobe Aufloesung)
        do l = igridfirstin + nstep, igridlastin - nstep, nstep
            xwert = (wvskal%nue(l) - wvskal%nue(igridfirstin)) * kwnenner
            tau_lev(l) = tau_lev(l) + yb + xwert * (slopel + xwert * &
              (3.0 * ycminyb - 2.0 * slopel - sloper + xwert * (-2.0 * ycminyb + slopel + sloper)))
            signaldec(l) = .true.
        end do
    end if

end do ! Linien

! Faltung wrktaua mit Gausskernel, Ergebnis zu wrktaub zuaddieren            
allocate (gausskernel(-ngauradius:ngauradius))
    
sumgau = 0.0d0
do k = -ngauradius,ngauradius
    deltanue = real(k,8) * wvskal%firstnue * wvskal%dnuerel
    gausskernel(k) = exp(-deltanue * deltanue / (bgau * bgau))
    sumgau = sumgau + gausskernel(k)
end do
gausskernel(:) = gausskernel(:) / sumgau

! Faltung Mittenbereich (keine Linienzentren am Rand), nur f�r Spektralpunkte mit Beitrag 
do k = 1 + ngauradius,wvskal%ngrid - ngauradius
    if (convdec(k)) then
        faltung = 0.0d0
        do l = -ngauradius,ngauradius
            faltung = faltung + gausskernel(l) * wrktaua(k-l)
        end do
        wrktaub(k) = wrktaub(k) + faltung
    end if
end do

deallocate (gausskernel)

! Interpolation Zwischenwerte in tau_lev
spkwnenner = 1.0 / real(nstep)
do k = nstep + 1,wvskal%ngrid - 2 * nstep,nstep
    if (signaldec(k - nstep) .or. signaldec(k + 2 * nstep)) then
        slopel = (tau_lev(k) - tau_lev(k - nstep))
        sloper = (tau_lev(k + 2 * nstep) - tau_lev(k + nstep))
        ycminyb = tau_lev(k + nstep) - tau_lev(k)
        do l = 1, nstep - 1
            xwert = real(l) * spkwnenner
            tau_lev(k + l) = tau_lev(k) + xwert * (slopel + xwert * &
              (3.0 * ycminyb - 2.0 * slopel - sloper + xwert * (-2.0 * ycminyb + slopel + sloper)))
        end do
    end if
end do

tau_lev = tau_lev + wrktaub

deallocate (signaldec,wrktaua,wrktaub)

end subroutine make_tau_lev



!====================================================================
!  subroutine make_tau_poly: polynomial approx to tau as fct of airmass
!====================================================================
subroutine make_tau_poly(sumtau,polytau)

use globvar24

implicit none

real,dimension(wvskal%ngrid,maxams),intent(in) :: sumtau
real,dimension(wvskal%ngrid,maxpoly),intent(inout) :: polytau

integer :: i,j,k,kpos,jpos
real(8) :: sumwert,guete,maxguete
real(8),dimension(maxams) :: airmass,vectorein
real(8),dimension(maxpoly) :: vectoraus
real(8),dimension(maxams,maxpoly) :: jak
real(8),dimension(maxpoly,maxams) :: matfinal
real(8),dimension(maxpoly,maxpoly) :: jtj,jtj_inv

! Matrix fuer Interpolation bestimmen
jak(:,1) = 1.0d0
do i = 2,maxpoly
    do j = 1,maxams
        airmass(j) = 1.0d0 / cos(obs%sza_gnd_rad(j))
        jak(j,i) = airmass(j) ** (2 * (i - 1))
    end do
end do

! JTJ
jtj = matmul(transpose(jak),jak)

! JTJ-1
call matinvers(jtj,jtj_inv,maxpoly)

! JTJ-1 * JT
matfinal= matmul(jtj_inv,transpose(jak))

!do i = 1,maxpoly
!    write (*,'(10(ES10.3))') (matfinal(i,j),j=1,maxams)
!end do

do j = 1,wvskal%ngrid
    vectorein = sumtau(j,1:maxams)
    vectoraus = matmul(matfinal,vectorein)
    polytau(j,1:maxpoly) = vectoraus
end do

! Kontrolliere Qualitaet der Interpolation

print *,'checking polynomial approx species... '
maxguete = 0.0
do j = 1,wvskal%ngrid
    do k = 1,maxams
        sumwert = polytau(j,1) + polytau(j,2) * airmass(k)**2 &
          + polytau(j,3) * airmass(k)**4 + polytau(j,4) * airmass(k)**6 &
          + polytau(j,5) * airmass(k)**8
        guete = abs(sumwert - sumtau(j,k)) / (sumtau(j,k) + 1.0e-8)
        if (guete .gt. maxguete) then
            maxguete = guete
            kpos = k
            jpos = j
        end if
        if (guete .gt. 1.0e-3) then
            print *,'nue_index n_ams: ',j,k
            print *,sumwert,sumtau(j,k)
            call warnout('imprecise interpolation!',1)
        end if
    end do
end do
print *,'nue_index n_ams maxerr: ',jpos,kpos,maxguete
print *,'... Done!'

end subroutine make_tau_poly



!====================================================================
!  function make_vnorm: calculates line strength of Voigt line
!====================================================================
real(8) function make_vnorm(lin_species,lin_nue,lin_ergniveau,lin_kappacm,Tkel)

use globvar24, only : amunit,clicht,kboltz

implicit none

integer,intent(in) :: lin_species
real,intent(in) :: lin_ergniveau,lin_kappacm
real(8),intent(in) :: lin_nue,Tkel

real(8) :: masseamu,qa,qb,qc,qd,qe,qf,qg,ntzunto,stimuess,qrel,xwert

! Gamache coeffs, mass
call infospecies(lin_species,masseamu,qa,qb,qc,qd,qe,qf,qg)
xwert = 8.3333333d-3 * (Tkel - 296.0d0)
qrel = exp(-xwert * (qa + xwert * (qb + xwert * (qc + xwert * &
  (qd + xwert * (qe + xwert * (qf + xwert * qg)))))))
ntzunto = qrel * exp(1.43877d0 * lin_ergniveau * (1.0d0 / 296.0d0 - 1.0d0 / Tkel))
stimuess = (1.0d0 - exp(-1.43877d0 * lin_nue / Tkel)) / (1.0d0 - exp(-4.86071d-3 * lin_nue))
make_vnorm = 1.0d-4 * lin_kappacm * ntzunto * stimuess  !per molecule

end function make_vnorm



!====================================================================
!  matinvers: invertiert eine symmetrische nmax x nmax Matrix
!====================================================================
subroutine matinvers(matein,mataus,nmax)

implicit none

integer,intent(in) :: nmax
real(8),dimension(nmax,nmax),intent(in) :: matein
real(8),dimension(nmax,nmax),intent(out) :: mataus

logical :: warnung
logical,dimension(nmax):: done
integer :: i,j,k,l,jj,kk,jk,lk,nrank,nvmax,icount
real(8) :: check
real(8) :: vkk,vjk,pivot
real(8),dimension(:),allocatable :: v

! Eindimensionale Darstellung der symmetrischen Eingabematrix in v
nvmax = (nmax * nmax + nmax) / 2
allocate (v(nvmax))

! Werte in v eintragen und diag eintragen
icount = 0
do i = 1,nmax ! Zeilenindex
    do j = 1,i ! Spaltenindex
        icount = icount + 1
        v(icount) = matein(j,i)
    end do
end do

! Berechnung der Inversen (nach Blobel / Lohrmann, S.67)
! reset flags
done(1:nmax) = .false.

! loop
nrank = 0
do i = 1,nmax

    ! search for pivot and test for linearity and zero matrix
    k = 0
    jj = 0
    vkk = 0.0d0

    ! groesstes verbliebenes Diagonalelement aufsuchen
    do j = 1,nmax
        jj = jj + j
        if (.not. done(j)) then
            if (k .eq. 0) k = j
            if (abs(v(jj)) .ge. vkk) then
                vkk = abs(v(jj))
                k = j
            end if
        end if
    end do
    done(k) = .true.

    ! kk is previous diagonal element
    kk = (k * k - k) / 2

    ! prepare exchange step
    nrank = nrank + 1
    pivot = 1.0d0 / v(kk+k)
    v(kk+k) = - pivot
    jj = 0

    ! exchange step
    jk = kk
    do j = 1,nmax
        if (j .le. k) jk = jk + 1
        if (j .gt. k) jk = jk + j - 1
        if (j .ne. k) then
            vjk = v(jk)
            v(jk) = pivot * vjk
            ! index of pivot row / column
            lk = kk
            do l = 1,j
                if (l .le. k) lk = lk + 1
                if (l .gt. k) lk = lk + l - 1
                if (l .ne. k) then
                    v(jj+l) = v(jj+l) - v(lk) * vjk
                end if
            end do
        end if
        jj = jj + j
    end do

end do

! Werte aus v austragen (Vorzeichenwechsel!)
jj = 0
do j = 1,nmax ! Zeilenindex
    jj = jj + j
    mataus(j,j) = -v(jj)
    do i = j+1,nmax ! Spaltenindex
        icount = j + i * (i - 1) / 2
        mataus(j,i) = -v(icount)
        mataus(i,j) = -v(icount)
    end do
end do

deallocate (v)

!Test: ist die Inverse gefunden?
warnung = .false.
do i = 1,nmax
    do j = 1,nmax
        check = 0.0d0
        do k = 1,nmax
            check = check + matein(i,k) * mataus(k,j)
        end do
        if (i .eq. j) then
            if (abs(check - 1.0d0) .gt. 1.0d-4) warnung = .true.
        else
            if (abs(check) .gt. 1.0d-4) warnung = .true.
        end if
    end do
end do
if (warnung) then
    print *,'subroutine matinvers: inverted matrix incorrect!'
end if

end subroutine matinvers



!====================================================================
!  next_free_unit
!====================================================================
integer function next_free_unit ()

implicit none

integer :: iu_free, status
logical :: is_open

iu_free = 9
is_open = .true.

do while (is_open .and. iu_free < 100)
    iu_free = iu_free+1
    inquire (unit=iu_free, opened=is_open, iostat=status)
    if (status .ne. 0) call warnout ('Error in inquiry!',0)
enddo

if (iu_free >= 100) call warnout ('No free unit < 100 found!',0)

next_free_unit = iu_free

end function next_free_unit



!====================================================================
!  subroutine prepare_solspec: calculates solar spectra on tau grid
!====================================================================
subroutine prepare_solspec(firstnue_solspec_inp,lastnue_solspec_inp,ngrid_solspec_inp,solspec_inp,solspec)

use globvar24

implicit none

integer,intent(in) :: ngrid_solspec_inp
real(8),intent(in) :: firstnue_solspec_inp,lastnue_solspec_inp
real,dimension(ngrid_solspec_inp),intent(in) :: solspec_inp 
real,dimension(wvskal%ngrid),intent(out) :: solspec

integer :: i,iactgrid
real(8) :: actnue,dnue,dnue_inv
real :: rest

dnue = (lastnue_solspec_inp - firstnue_solspec_inp) / real(ngrid_solspec_inp - 1,8)
dnue_inv = 1.0d0 / dnue

do i = 1,wvskal%ngrid
    ! polynomial fit 
    actnue = wvskal%nue(i)
    iactgrid = int((actnue - firstnue_solspec_inp) * dnue_inv) + 1
    rest = (actnue - firstnue_solspec_inp - (iactgrid - 1) * dnue) * dnue_inv
    solspec(i) = solspec_inp(iactgrid) + 0.5 * rest * ((solspec_inp(iactgrid+1) - solspec_inp(iactgrid-1)) &
      + rest * (2.0 * solspec_inp(iactgrid-1) &
      - 5.0 * solspec_inp(iactgrid) + 4.0 * solspec_inp(iactgrid+1) - solspec_inp(iactgrid+2)) &
      + rest * rest * (-solspec_inp(iactgrid-1) + 3.0 * solspec_inp(iactgrid) &
      - 3.0 * solspec_inp(iactgrid+1) + solspec_inp(iactgrid+2)))
end do

end subroutine prepare_solspec



!====================================================================
!  subroutine raytrace: determines raypath
!====================================================================
subroutine raytrace(h_lev_m,p_lev_pa,T_lev_K,latrad,azirad,sza_rad,astrodec,sza_lev_rad)

use globvar24

implicit none


real(8),dimension(n_lev),intent(in) :: h_lev_m,p_lev_pa,T_lev_K
real(8),intent(in) :: latrad,azirad,sza_rad
logical,intent(in) :: astrodec
real(8),dimension(n_lev),intent(out) :: sza_lev_rad

integer :: i
real(8) :: axa,bxb,wert,Mradius,Nradius,Reff,refindex,sphereconst,dsza,elev_grad

! determine effective Radius of Earth (as function of geographical latitude and azimuth)
axa = Rearth_equat * Rearth_equat
bxb = Rearth_pol * Rearth_pol
wert = axa * cos(latrad) * cos(latrad) + bxb * sin(latrad) * sin(latrad)
Mradius = (axa * bxb) / sqrt(wert * wert * wert)
Nradius = axa / sqrt(wert)
Reff = 1.0d0 / ((cos(azirad) * cos(azirad)) / Mradius + (sin(azirad) * sin(azirad)) / Nradius)
!Reff = 6.371d6

! astrodec = F input of astronomical angle at observer, T input of apparent refracted angle at observer
if (astrodec) then
    ! set start value at observer to input apparent refracted angle
    sza_lev_rad(1) = sza_rad
else
    ! Use standard refraction formula to estimate apparent angle at observer
    ! taken from Meeus,1994
    ! numerical factor is 1.02 * 283K / 101000 Pa * conversion arcmin to rad
    elev_grad = radtograd * (0.5d0 * pi - sza_rad)
    dsza = 8.15d-7 / tan(gradtorad * (elev_grad + 10.3d0 / (elev_grad + 5.11d0))) * p_lev_pa(1) / T_lev_K(1)
    sza_lev_rad(1) = sza_rad - dsza
end if

refindex = 1.0d0 + (7.7518d-7 + &
  4.5814d-17 * (wvskal%nueraytra - 100.0d0) * (wvskal%nueraytra - 100.0d0)) * p_lev_pa(1) / T_lev_K(1)
sphereconst = refindex * (Reff + h_lev_m(1)) * sin(sza_lev_rad(1))

do i = 2,n_lev
    refindex = 1.0d0 + (7.7518d-7 + &
      4.5814d-17 * (wvskal%nueraytra - 100.0d0) * (wvskal%nueraytra - 100.0d0)) * p_lev_pa(i) / T_lev_K(i)
    sza_lev_rad(i) = asin(sphereconst / (refindex * (Reff + h_lev_m(i))))
end do

end subroutine raytrace



!====================================================================
!  readhitran: reads linedata for all species in all MWs
!====================================================================
subroutine read_hitran_lbl()

use globvar24
use globlin24

implicit none

character(len=100) :: zeile
logical :: decreadiso,dechit08,decinroi,dateidadec,LMdec,SDVdec
integer :: i,iroi,j,zaehler,hitspecies,iowert,dumint,iunit_fwd,next_free_unit
real :: LMa,LMb,LMc,LMY,LMTK1,LMTK2,gam2ratio,gam2Tdep,dumreal
real(8) :: hitnue,hitkappacm,hitdummy,hitlorwidthf &
  ,hitlorwidths,hitergniveau,hitlortdepend,hitpshift &
  ,lownue_read,highnue_read,dumdble,masseamu,qa,qb,qc,qd,qe,qf,qg

lownue_read = wvskal%firstnue + 25.1
highnue_read = wvskal%lastnue - 25.1

masseamu_min(1:n_tau) = 1.0d5
zaehler = 0

! check regions of interest
inquire (file = 'inp_fast'//pathstr//'roi.inp',exist = dateidadec)
if (dateidadec) then
    print *,"The ROI specification file is present!"
    iunit_fwd = next_free_unit()
    open (iunit_fwd,file = 'inp_fast'//pathstr//'roi.inp',status = 'old',action = 'read')
    call gonext(iunit_fwd,.false.)
    read (iunit_fwd,*) n_roi
    if (n_roi .gt. maxroi) then
        call warnout('n_roi > maxroi',0)
        print *,'n_roi: ',n_roi
        print *,'maxroi:',maxroi
    end if
    call gonext(iunit_fwd,.false.)
    do iroi = 1,n_roi
        read (iunit_fwd,*) nueroi(iroi)
    end do
    close (iunit_fwd)
else
    print *,"No ROI specification file found!"
    n_roi = 1
    nueroi(1) = cmplx(wvskal%firstnue,wvskal%lastnue)
end if

do i = 1,n_tau

    print *,'Reading lines from ASCII HITRAN file... species:',i

    ! test whether HITRAN file is accessible, test format
    iunit_fwd = next_free_unit()
    open (iunit_fwd,file = hitdatei(i),iostat = iowert,status = 'old',action = 'read')

    if (iowert .ne. 0) then
        print *,'Cannot read HITRAN file:'
        print *,hitdatei(i)
        stop
    end if
    
    close (iunit_fwd)

    print *,'Reading HITRAN file:'
    print *,hitdatei(i)
    iunit_fwd = next_free_unit()
    open (iunit_fwd,file = hitdatei(i),iostat = iowert,status = 'old')

    lines%lb(i) = zaehler + 1

    do ! read through line data file
        
        LMdec = .false.
        LMY = 0.0
        LMTK1 = 0.0
        LMTK2 = 0.0
        SDVdec = .false.
        gam2ratio = 0.0
        gam2Tdep = 0.0

        zeile = ''
        read (iunit_fwd,'(A100)',end = 102) zeile
        read (zeile,802) hitspecies

        if (hitspecies .eq. 997) then ! Line Mixing
            LMdec = .true.
            read (zeile,803) dumint,LMa,LMb,LMc
            LMY = LMb
            LMTK1 = 0.5 * (LMc - LMa)
            LMTK2 = 0.5 * (LMa + LMc) - LMb
            !print *,LMa,LMb,LMc
            !call warnout ('LM entry found!',1)
            zeile = ''
            read (iunit_fwd,'(A100)') zeile
            read (zeile,802) hitspecies
        end if
        
        if (hitspecies .eq. 998) then ! SDV
            SDVdec = .true.
            read (zeile,803) dumint,gam2ratio,gam2Tdep,dumreal
            zeile = ''
            read (iunit_fwd,'(A100)') zeile
        end if

        if (zeile(41:41) .eq. '.') then ! Check HIT08 format, read HITRAN parameters
            dechit08 = .false.
        else
            if (zeile(42:42) .eq. '.') then
                !print *,'HIT08 format detected!'
                dechit08 = .true.
            else
                print*, zeile(1:50)
                call warnout('Incompatible HIT format!',0)
            end if
        end if

        if (dechit08) then
            read (zeile,801) hitspecies,hitnue,hitkappacm,hitdummy &
              ,hitlorwidthf,hitlorwidths,hitergniveau,hitlortdepend,hitpshift
        else
            read (zeile,800) hitspecies,hitnue,hitkappacm,hitdummy &
              ,hitlorwidthf,hitlorwidths,hitergniveau,hitlortdepend,hitpshift
        end if

        if (hitnue .gt. highnue_read) exit

        ! check whether line inside region of interest
        decinroi = .false.
        if (hitnue .gt. lownue_read) then
            do iroi = 1,n_roi
                if ((hitnue - real(nueroi(iroi),8)) * (aimag(nueroi(iroi)) - hitnue) .ge. 0.0d0) decinroi = .true.
            end do
        end if

        if (decinroi .and. hitkappacm .ge. clipweakline(i)) then

            ! Selection of isotopologues
            if (iso_handle(i) .eq. 0) then
                decreadiso = .true.
            else
                decreadiso = .false.
                if (iso_handle(i) .gt. 0) then
                    do j = 1,iso_handle(i)
                        if ((hitspecies - iso_kennung(j,i)) .eq. 0) decreadiso = .true.
                    end do
                else
                    if ((hitspecies - iso_kennung(1,i)) .ge. 0) decreadiso = .true.
                end if
            end if

            ! read line if isotopic species selected
            if (decreadiso) then

                zaehler = zaehler + 1

                if (zaehler .gt. maxlines) then
                    print *,'Maximal allowed number of lines ',maxlines
                    print *,'Reading species:',i
                    call warnout('readhitran: too many lines!',0)
                end if

                lines%LMdec(zaehler) = LMdec
                lines%LMY(zaehler) = LMY
                lines%LMTK1(zaehler) = LMTK1
                lines%LMTK2(zaehler) = LMTK2
                lines%SDVdec(zaehler) = SDVdec
                lines%gam2ratio(zaehler) = gam2ratio
                lines%gam2Tdep(zaehler) = gam2Tdep
                lines%species(zaehler) = hitspecies
                lines%nue(zaehler) =  hitnue
                lines%kappacm(zaehler) = hitkappacm
                lines%lorwidthf(zaehler) = hitlorwidthf
                lines%ergniveau(zaehler) = hitergniveau
                lines%lortdepend(zaehler) = hitlortdepend
                lines%pshift(zaehler) = hitpshift

                ! self-broadening
                ! For any species apart from H2O (all isos) overwrite self-broadening
                ! with 1.27x foreign-broadening
                if ((18 - lines%species(zaehler)) * (lines%species(zaehler) - 11) .ge. 0) then
                    lines%lorwidths(zaehler) = hitlorwidths
                else
                    lines%lorwidths(zaehler) = 1.35d0 * hitlorwidthf
                end if

                ! Gaussian width at reference T (296 K)
                call infospecies(lines%species(zaehler),masseamu,qa,qb,qc,qd,qe,qf,qg)
                if (masseamu .lt. masseamu_min(i)) masseamu_min(i) = masseamu

            end if ! select isotolopogue

        end if  ! if inside spectral bounds

    end do ! read through linedata file

    102 continue

    close (iunit_fwd)

    lines%rb(i) = zaehler

    print *,'Line pointer and nof lines for species: ',i
    print *, lines%lb(i),lines%rb(i),lines%rb(i) - lines%lb(i) + 1

end do ! species

print*,'...reading lines from HITRAN file completed!'

800 format(I3,F12.6,E10.3,E10.3,F5.4,F5.4,F10.4,F4.2,F8.6)  ! old HIT format
801 format(I3,F12.6,E10.3,E10.3,F6.5,F4.3,F10.4,F4.2,F8.6)  ! HIT 08 format
802 format(I3,F12.6) ! Zeilenanfang
803 format(I3,1X,E10.3,1X,E10.3,1X,E10.3) ! Zusatzparameter

end subroutine read_hitran_lbl



!====================================================================
!  read_levels: read predefined altitude scheme from file
!====================================================================
subroutine read_levels(infile)

use globvar24
use globlev24

implicit none

character(len=*),intent(in) :: infile

integer :: i,iowert,iunit_fwd,next_free_unit

iunit_fwd = next_free_unit()
open (iunit_fwd,file = infile,iostat = iowert,status = 'old',action = 'read')
if (iowert .ne. 0) then
    print *,'Cannot read input file:    '
    print *,infile
end if

! model atmosphere general
call gonext(iunit_fwd,.false.)
read (iunit_fwd,*) n_lev
print *,'Number of levels:               ',n_lev

if (n_lev .gt. maxlev) then
    print *,'n_lev:',n_lev
    print *,'maxlev:',maxlev
    print *,'n_lev set to maxlev!'
    n_lev = maxlev
    call warnout('n_lev > maxlev',1)
end if

call gonext(iunit_fwd,.false.)
read (iunit_fwd,*) (lev%h_m(i),i = 1,n_lev)

if (abs(lev%h_m(1)) .gt. 0.0001) then
    print *,lev%h_m(1)
    call warnout('Warning: incr h(1) differs from 0!',1)
end if

! convert to m, add observer altitude
do i = 1,n_lev
    lev%h_m(i) = 1.0d3 * lev%h_m(i) + obs%h_m
end do

print *,'Level altitudes [m]:'
write (*,'(5(ES11.4))') (lev%h_m(i),i = 1,n_lev)

close (iunit_fwd)

end subroutine read_levels



!====================================================================
!  read_input_fwd: read general input for precalc of xs from input file
!====================================================================
subroutine read_pcxsinput(infile)

use globvar24

implicit none

character(len=*),intent(in) :: infile

character(len=8) :: inpchar
integer :: iowert,i,j,iunit_fwd,next_free_unit
real(8) :: alti_km,latgrad,longrad
complex(8) :: mwbds

iunit_fwd = next_free_unit()
open (iunit_fwd,file = infile,iostat = iowert,status = 'old',action = 'read')

if (iowert .ne. 0) then
    print *,'Cannot read input file:    '
    print *,infile
end if

! observer location and altitude
call gonext(iunit_fwd,.false.)
read (iunit_fwd,*) alti_km
obs%h_m = 1000.0 * alti_km
read (iunit_fwd,*) latgrad
obs%lat_rad = gradtorad * latgrad
read (iunit_fwd,*) longrad
obs%lon_rad = gradtorad * longrad
read (iunit_fwd,*) obs%p_hPa
print *,'Observer altitude:         ',obs%h_m
print *,'Observer latitude:         ',latgrad
print *,'Observer longitude:        ',longrad
print *,'Observer pressure:         ',obs%p_hPa

! pT file
call gonext(iunit_fwd,.false.)
read (iunit_fwd,'(A)') datumspfad
read (iunit_fwd,'(A)') sitename
read (iunit_fwd,'(A)') yymmddchar
read (iunit_fwd,*) filesoutdec
read (iunit_fwd,*) quietrundec
read (iunit_fwd,'(A)') pTdatei
read (iunit_fwd,*) pThumdec
read (iunit_fwd,*) n_Tdisturb
print *,'date folder:               ',datumspfad
print *,'site name:                 ',sitename
print *,'yymmddchar:                ',yymmddchar
print *,'filesoutdec:               ',filesoutdec
print *,'quietoutdec:               ',quietrundec
print *,'pT-file:                   ',pTdatei
print *,'pThumdec:                  ',pThumdec
print *,'n_Tdisturb:                ',n_Tdisturb

! ceck consistency of datumspfad, pTdatei and yymmddcar
if (index(datumspfad,yymmddchar) .eq. 0) then
    print *,datumspfad
    print *,yymmddchar
    call warnout('inconsistent date folder!',1)
end if
if (index(pTdatei,yymmddchar) .eq. 0) then
    print *,ptdatei
    print *,yymmddchar
    call warnout('inconsistent pT folder!',1)
end if
! solar spectrum
call gonext(iunit_fwd,.false.)
read (iunit_fwd,'(A)') soldatei
read (iunit_fwd,*) obs%FOVext
print *,'pT file:                   ',pTdatei
print *,'fractional external FOV:   ',obs%FOVext

! line lists (H2O,HDO,CO2,N2O,CO,CH4,O2,HF,HCl)
call gonext(iunit_fwd,.false.)
read (iunit_fwd,*) n_tau
if (n_tau .gt. maxtau) then
    print *,'maxtau:  ',maxtau
    print *,'n_tau:   ',n_tau
    call warnout('n_tau>maxtau',0)
else
    print *,'n_tau:',n_tau
end if

call gonext(iunit_fwd,.false.)
do i = 1,n_tau
    read (iunit_fwd,'(A)') hitdatei(i)
    print *, hitdatei(i)
    read (iunit_fwd,*) iso_handle(i)
    print *, 'iso_handle:',iso_handle(i)
    if (iso_handle(i) .gt. maxiso) then
        print *,'iso handle:',iso_handle(i)
        print *,'max iso   :',maxiso
        call warnout('Too many isotopic species!',0)
    end if
    ! if handle = 0, all isos are collected, no reading here
    ! if handle >= 1, select specified number of isos
    if (iso_handle(i) .ge. 1) then
        do j = 1,iso_handle(i)
            read (iunit_fwd,*) iso_kennung(j,i)
        end do
    end if
    ! if handle = -1, all isos beyond the mark are collected
    if (iso_handle(i) .eq. -1) then
        read (iunit_fwd,*) iso_kennung(1,i)
    end if
end do

! VMR profiles (H2O,HDO,CO2,N2O,CO,CH4,O2,HF,HCl)
call gonext(iunit_fwd,.false.)
print *,''
print *,'VMR files:                      '
do i = 1,n_tau
    read (iunit_fwd,'(A)') vmrdatei(i)
    read (iunit_fwd,'(L)') wetdec(i)
    print *,trim(vmrdatei(i))
    print *,'iswetdec: ',wetdec(i)
    print *,''
end do

! AVK calculation
call gonext(iunit_fwd,.false.)
print *,'AVK calculation:'
do i = 1,n_tau
    read (iunit_fwd,*) nsens(i)
    if (nsens(i) .gt. maxsens) then
        print *,'nsens:',nsens(i)
        print *,'maxsens:',maxsens
        call warnout('Too many AVK MWs!',0)
    end if
    do j = 1,nsens(i)
        read (iunit_fwd,'(A)') inpchar
        mw(j,i)%gasname = trim(inpchar)
        print *,'gas name, gas number for AVK calc:',mw(j,i)%gasname
        read (iunit_fwd,*) mwbds
        mw(j,i)%firstnue_inp = min(real(mwbds,8),aimag(mwbds))
        mw(j,i)%lastnue_inp = max(real(mwbds,8),aimag(mwbds))
        print *,'requested microwindow bounds:',mwbds
    end do    
end do

! check MW bounds, coarse grid pointer (factor ngridratio)
do i = 1,n_tau
    do j = 1,nsens(i)
        if (mw(j,i)%firstnue_inp .lt. wvskal%firstnue + 25.1d0) call warnout ("MW bound too low!",0)
        if (mw(j,i)%lastnue_inp .gt. wvskal%lastnue - 25.1d0) call warnout ("MW bound too high!",0)
        mw(j,i)%istart = log(mw(j,i)%firstnue_inp / wvskal%firstnue) / wvskal%dnuerel + 1
        mw(j,i)%istop = log(mw(j,i)%lastnue_inp / wvskal%firstnue) / wvskal%dnuerel + 1
        ! readjust istop for matching coarse grid
        mw(j,i)%istop = mw(j,i)%istart + ngridratio &
          * int((mw(j,i)%istop - mw(j,i)%istart) / real(ngridratio,8))
        mw(j,i)%nfine = 1 + mw(j,i)%istop - mw(j,i)%istart
        mw(j,i)%ncoarse = 1 + (mw(j,i)%istop - mw(j,i)%istart) / ngridratio
    end do
end do

close (iunit_fwd)

end subroutine read_pcxsinput



!====================================================================
!  read_pT: read and interpolate T(z) profile to specified altitude grid
!====================================================================
subroutine read_pT(ptdatei,pobs_hPa,n_lev,h_lev_m,T_K,p_Pa,vmr_h2o_ppm,vmr_hdo_ppm)

implicit none

integer,parameter :: npT_max = 137

character(len=*),intent(in) :: pTdatei
real(8) :: pobs_hPa 
integer,intent(in) :: n_lev
real(8),dimension(n_lev),intent(in) :: h_lev_m
real(8),dimension(n_lev),intent(out) :: T_K,p_Pa,vmr_h2o_ppm,vmr_hdo_ppm

character(len=300) :: zeile
logical :: readmapdec
integer :: i,j,inear,iowert,nhead,ncol,npT,nJD,ipTleft,ipTright &
  ,istrato,mapversion,iunit_fwd,next_free_unit
real(8) :: lnp,dumreal,dh,pwert,pleft,pright,rest,faktor,korrfaktor
real(8),dimension(npT_max) :: hinp_m,Tinp_K,pinp_Pa,vmrinph2o_ppm,vmrinphdo_ppm

! decide whether *.map or *.prf file

i = index(pTdatei,'.map')
j = index(pTdatei,'.prf')
if (i + j .eq. 0) then
    call warnout('unrecognized pT file!',0)
end if

if (i .gt. 0) then
    readmapdec = .true.
else
    readmapdec = .false.
end if

if (readmapdec) then ! read from GFIT map file

    ! open file
    iunit_fwd = next_free_unit()
    open (iunit_fwd,file = ptdatei,iostat = iowert,status = 'old')
    if (iowert .ne. 0) then
        print *,'pT file:',pTdatei
        call warnout('Cannot read pT file!',0)
    end if

    ! read number of header lines and data columns
    read (iunit_fwd,*) nhead,ncol
    if (nhead .eq. 11) mapversion = 0 ! GGG14 format
    if (nhead .eq. 12) mapversion = 1 ! GGG20 format
    do i = 2,nhead - 1
        read (iunit_fwd,'(A)') zeile
    end do

    if (mapversion .eq. 0) then
        if (zeile(1:63) .ne. ' Height,Temp,Pressure,Density,h2o,hdo,co2,n2o,co,ch4,hf,gravity') then
            call warnout('Unexpected map-file ver0 structure!',0)
        end if
        read (iunit_fwd,'(A)') zeile
        if (zeile(1:60) .ne. ' km,K,hPa,molecules_cm3,parts,parts,ppm,ppb,ppb,ppb,ppt,m_s2') then
            call warnout('Unexpected map-file ver0 structure!',0)
        end if
        if (ncol .ne. 12) then
            call warnout('Unexpected map-file ver0 structure!',0)
        end if
    end if

    if (mapversion .eq. 1) then
        if (zeile(1:66) .ne. 'Height,Temp,Pressure,Density,h2o,hdo,co2,n2o,co,ch4,hf,o2,gravity') then
            call warnout('Unexpected map-file ver1 structure!',0)
        end if
        read (iunit_fwd,'(A)') zeile
        if (zeile(1:66) .ne. 'km,K,hPa,molecules_cm3,parts,parts,ppm,ppb,ppb,ppb,ppt,parts,m_s2') then
            call warnout('Unexpected map-file ver1 structure!',0)
        end if
        if (ncol .ne. 13) then
            call warnout('Unexpected map-file ver1 structure!',0)
        end if
    end if

    ! determine number of data lines
    npT = 0
    do
        read (iunit_fwd,'(A)',end=103) zeile
        npT = npT + 1
    end do
    103 continue

    close (iunit_fwd)

    if (npT .gt. npT_max) then
        print *,npT,npT_max
        call warnout('Too many levels in map file!',0)
    end if

    ! read data
    iunit_fwd = next_free_unit()
    open (iunit_fwd,file = ptdatei,iostat = iowert,status = 'old')

    do i = 1,nhead
        read (iunit_fwd,'(A)') zeile
    end do
    zeile = ''    
    do i = 1,npT
        read (iunit_fwd,'(A)') zeile
        read (zeile,*) hinp_m(i),Tinp_K(i),pinp_Pa(i) &
          ,dumreal,vmrinph2o_ppm(i),vmrinphdo_ppm(i)
    end do

    ! conversion of units
    pinp_Pa(1:npT) = 1.0d2 * pinp_Pa(1:npT) ! hPa to Pa
    hinp_m(1:npT) = 1.0d3 * hinp_m(1:npT) ! km to m
    vmrinph2o_ppm(1:npT) = 1.0d6 * vmrinph2o_ppm(1:npT) ! to ppm
    vmrinphdo_ppm(1:npT) = 1.0d6 * vmrinphdo_ppm(1:npT) ! to ppm

    close (iunit_fwd)

else ! read from PROFFIT *.prf file

    vmrinph2o_ppm(1:npT_max) = 0.0d0
    vmrinphdo_ppm(1:npT_max) = 0.0d0

    ! open file, process standard part of file
    iunit_fwd = next_free_unit()
    open (iunit_fwd,file = ptdatei,iostat = iowert,status = 'old')
    if (iowert .ne. 0) then
        print *,'pT file:',pTdatei
        call warnout('Cannot read pT file!',0)
    end if

    call gonext(iunit_fwd,.false.)
    read (iunit_fwd,*) npT
    if (npT .gt. npT_max) then
        print *,'Max levels for p/T input:',npT_max
        call warnout('Read_pT: Too many levels in p/T file!',0)
    end if

    call gonext(iunit_fwd,.false.)
    read (iunit_fwd,*) (hinp_m(i),i = 1,npT)
    hinp_m(1:npT) = 1.0d3 * hinp_m(1:npT) ! km to m

    call gonext(iunit_fwd,.false.)
    read (iunit_fwd,*) (pinp_Pa(i),i = 1,npT)
    pinp_Pa(1:npT) = 1.0d2 * pinp_Pa(1:npT) ! hPa to Pa

    call gonext(iunit_fwd,.false.)
    read (iunit_fwd,*) (Tinp_K(i),i = 1,npT)

    close (iunit_fwd)

end if

! interpolation / extrapolation of daily T to model levels
do i = 1,n_lev
    ! downward extrapolation
    if (h_lev_m(i) .lt. hinp_m(1)) then
        faktor = (h_lev_m(i) - hinp_m(1)) / (hinp_m(2) - hinp_m(1))
        T_K(i) = Tinp_K(1) + (Tinp_K(2) - Tinp_K(1)) * faktor
        vmr_h2o_ppm(i) = vmrinph2o_ppm(1) + (vmrinph2o_ppm(2) - vmrinph2o_ppm(1)) * faktor
        vmr_hdo_ppm(i) = vmrinphdo_ppm(1) + (vmrinphdo_ppm(2) - vmrinphdo_ppm(1)) * faktor
    else
        if (h_lev_m(i) .gt. hinp_m(npT)) then
            ! upward extrapolation
            T_K(i) = Tinp_K(npT)
            vmr_h2o_ppm(i) = vmrinph2o_ppm(npT)
            vmr_hdo_ppm(i) = vmrinphdo_ppm(npT)
        else
            ! interpolation
            inear = 1
            do while (hinp_m(inear+1) .lt. h_lev_m(i) .and. inear .lt. npT)
                inear = inear + 1
            end do
            faktor = (h_lev_m(i) - hinp_m(inear)) / (hinp_m(inear+1) - hinp_m(inear))
            T_K(i) = Tinp_K(inear) + (Tinp_K(inear+1) - Tinp_K(inear)) * faktor
            vmr_h2o_ppm(i) = vmrinph2o_ppm(inear) + &
              (vmrinph2o_ppm(inear+1) - vmrinph2o_ppm(inear)) * faktor
            vmr_hdo_ppm(i) = vmrinphdo_ppm(inear) + &
              (vmrinphdo_ppm(inear+1) - vmrinphdo_ppm(inear)) * faktor
            lnp = log(pinp_Pa(inear)) + log(pinp_Pa(inear+1) / pinp_Pa(inear)) * faktor
            p_Pa(i) = exp(lnp)
        end if
    end if
end do

! interpolate for pressure at station level
if (h_lev_m(1) .lt. hinp_m(1)) then
    ! downward extrapolation
    print *,'Warning: ground p + T extrapolated!!'
    lnp = log(pinp_Pa(1)) + log(pinp_Pa(2) / pinp_Pa(1)) * &
      (h_lev_m(1) - hinp_m(1)) / (hinp_m(2) - hinp_m(1))
    p_Pa(1) = exp(lnp)
else
    ! interpolation
    inear = 1
    do while (hinp_m(inear+1) .lt. h_lev_m(1) .and. inear .lt. npT)
        inear = inear + 1
    end do
    lnp = log(pinp_Pa(inear)) + log(pinp_Pa(inear+1) / pinp_Pa(inear)) * &
    (h_lev_m(1) - hinp_m(inear)) / (hinp_m(inear+1) - hinp_m(inear))
     p_Pa(1) = exp(lnp)
end if

! construct approx hydrostatic atmosphere
do i = 2,n_lev
    dh = 29.3d0 * 0.5d0 * (T_K(i-1) + T_K(i))
    p_Pa(i) = p_Pa(i-1) * exp(-(h_lev_m(i) - h_lev_m(i-1)) / dh)
end do

! correct pressure at observer, if applicable
if (pobs_hPa .lt. 9999.0) then
    if (abs(p_Pa(1) - 100.0d0 * pobs_hPa) .gt. 1000.0d0) then
        print *,'observer level pressure from pT file: ',0.01d0 * p_Pa(1)
        print *,'observer level pressure from input:   ',pobs_hPa
        call warnout ('Large pressure correction!',1)
    end if
    korrfaktor = 100.0d0 * pobs_hPa / p_Pa(1)
    p_Pa(:) = korrfaktor * p_Pa(:)
end if

! check resulting p,T profile
! check p
do i = 1,n_lev
    if (p_Pa(i) .lt. 9.0d4 * exp(-(h_lev_m(i)) / 5.8d3)) then
        print *,"level:",i
        print *,"pressure:",p_Pa(i)
        call warnout ("Model pressure too low!",0)
    end if
    if (p_Pa(i) .gt. 1.2d5 * exp(-(h_lev_m(i)) / 9.7d3)) then
        print *,"level:",i
        print *,"pressure:",p_Pa(i)
        call warnout ("Model pressure too high!",0)
    end if    
end do
! check T
do i = 1,n_lev
    if (T_K(i) .lt. 150.0d0) then
        print *,"level:",i
        print *,"T:",T_K(i)
        call warnout ("Model T too low!",0)
    end if
    if (T_K(i) .gt. 500.0d0) then
        print *,"level:",i
        print *,"T:",T_K(i)
        call warnout ("Model T too high!",0)
    end if    
end do

if (.not. readmapdec) then

    ! find thermo tropopause (lapse rate < -2K / km)
    istrato = n_lev
    do i = 1,n_lev - 1
        if (p_Pa(i) .lt. 4.0d4 .and. (T_K(i+1) - T_K(i)) / (h_lev_m(i+1) - h_lev_m(i)) .gt. -2.0d-3) then
            istrato = i
            exit
        end if
    end do

    do i = 1,istrato - 1
        ! assume 50% RH, apply Tetens formula
        vmr_h2o_ppm(i) = 3.054d8 * exp(17.27 * (T_K(i) - 273.15) / (T_K(i) - 35.85)) / p_Pa(i)
        vmr_hdo_ppm(i) = vmr_h2o_ppm(i) * (0.8d0 - 0.4d0 *  h_lev_m(i) / h_lev_m(istrato))
    end do
    do i = istrato,n_lev
        vmr_h2o_ppm(i) = 0.5 * (vmr_h2o_ppm(i-1) + 5.0d0)
        vmr_hdo_ppm(i) = 0.4d0 * vmr_h2o_ppm(i)
    end do
end if

print *,'pT, H2O, HDO profiles after read_pT:'
do i = 1,n_lev
    write (*,'(5(ES11.4))') h_lev_m(i),T_K(i),p_Pa(i),vmr_h2o_ppm(i),vmr_hdo_ppm(i)
end do

end subroutine read_pT



!====================================================================
!  read_solspec: read solar spectrum
!====================================================================
subroutine read_solspec(FOVext,ngrid_solspec_inp,solspec_inp)

use globvar24, only : soldatei

implicit none

integer,intent(in) :: ngrid_solspec_inp
real,intent(in) :: FOVext
real,dimension(ngrid_solspec_inp),intent(out) :: solspec_inp

integer :: i,iunit_fwd,next_free_unit
real :: dummy,wertcenter,wertintegral

iunit_fwd = next_free_unit()
open (iunit_fwd,file = soldatei,status = 'old',action = 'read')

call gonext(iunit_fwd,.false.)
call gonext(iunit_fwd,.false.)

do i = 1,ngrid_solspec_inp
    read (iunit_fwd,*) dummy,wertcenter,wertintegral
    solspec_inp(i) = (1.0 - FOVext) * wertcenter + FOVext * wertintegral
end do

close (iunit_fwd)

end subroutine read_solspec



!====================================================================
!  read_vmr: read vmr-Files
!====================================================================
subroutine read_vmr(vmrdatei,ispeci,n_lev,h_lev_m,vmr_lev)

implicit none

character(len=*),intent(in) :: vmrdatei
integer,intent(in) :: ispeci,n_lev
real(8),dimension(n_lev),intent(in) :: h_lev_m
real(8),dimension(n_lev),intent(out) :: vmr_lev

character(len=300) :: zeile
integer,parameter :: nvmr_max = 137
integer,parameter :: nJD_max = 100
logical :: readmapdec,flagdown
integer :: i,j,ipos,iowert,nhead,ncol,nvmr,inear,nJD,ivmrleft &
  ,ivmrright,mapversion,iunit_fwd,next_free_unit
real(8) :: rest,conversion,konstante,dumreal
real(8),dimension(nvmr_max) :: hinp_m,vmrinp

i = index(vmrdatei,'.map')
j = index(vmrdatei,'.prf')
if (i + j .eq. 0) then
    call warnout('unrecognized vmr file!',0)
end if

if (i .gt. 0) then
    readmapdec = .true.
else
    readmapdec = .false.
end if

if (readmapdec) then

    ! open file
    iunit_fwd = next_free_unit()
    open (iunit_fwd,file = vmrdatei,iostat = iowert,status = 'old')
    if (iowert .ne. 0) then
        print *,'vmr file:',vmrdatei
        call warnout('Cannot read vmr file!',0)
    end if

    ! read number of header lines and data columns
    read (iunit_fwd,*) nhead,ncol
    if (nhead .eq. 11) mapversion = 0 ! GGG14 format
    if (nhead .eq. 12) mapversion = 1 ! GGG20 format
    do i = 2,nhead - 1
        read (iunit_fwd,'(A)') zeile
    end do

    if (mapversion .eq. 0) then
        if (zeile(1:63) .ne. ' Height,Temp,Pressure,Density,h2o,hdo,co2,n2o,co,ch4,hf,gravity') then
            call warnout('Unexpected map-file ver0 structure!',0)
        end if
        read (iunit_fwd,'(A)') zeile
        if (zeile(1:60) .ne. ' km,K,hPa,molecules_cm3,parts,parts,ppm,ppb,ppb,ppb,ppt,m_s2') then
            call warnout('Unexpected map-file ver0 structure!',0)
        end if
        if (ncol .ne. 12) then
            call warnout('Unexpected map-file ver0 structure!',0)
        end if
    end if

    if (mapversion .eq. 1) then
        if (zeile(1:66) .ne. 'Height,Temp,Pressure,Density,h2o,hdo,co2,n2o,co,ch4,hf,o2,gravity') then
            call warnout('Unexpected map-file ver1 structure!',0)
        end if
        read (iunit_fwd,'(A)') zeile
        if (zeile(1:66) .ne. 'km,K,hPa,molecules_cm3,parts,parts,ppm,ppb,ppb,ppb,ppt,parts,m_s2') then
            call warnout('Unexpected map-file ver1 structure!',0)
        end if
        if (ncol .ne. 13) then
            call warnout('Unexpected map-file ver1 structure!',0)
        end if
    end if

    ! determine number of data lines
    nvmr = 0
    do
        read (iunit_fwd,'(A)',end=103) zeile
        nvmr = nvmr + 1
    end do
    103 continue

    close (iunit_fwd)

    if (nvmr .gt. nvmr_max) then
        print *,nvmr,nvmr_max
        call warnout('Too many levels in map file!',0)    
    end if

    konstante = 0.0
    select case (ispeci)
        case (1) ! H2O
            ipos = 1
            conversion = 1.0e6
        case (2) ! HDO
            ipos = 2
            conversion = 1.0e6
        case (3) ! CO2
            ipos = 3
            conversion = 1.0
        case (4) ! CH4
            ipos = 6
            conversion = 1.0e-3
        case (5) ! N2O
            ipos = 4
            conversion = 1.0e-3
        case (6) ! CO
            ipos = 5
            conversion = 1.0e-3
        case (7) ! O2 (missing in map file ver 0)
            if (mapversion .eq. 0) then
                ipos = 3
                conversion = 0.0
                konstante = 0.2095 * 1.0e6
            end if
            if (mapversion .eq. 1) then
                ipos = 8
                conversion = 1.0e6
            end if
        case (8) ! HF
            ipos = 7
            conversion = 1.0e-6
    end select

    ! read data
    iunit_fwd = next_free_unit()
    open (iunit_fwd,file = vmrdatei,iostat = iowert,status = 'old')

    do i = 1,nhead
        read (iunit_fwd,'(A)') zeile
    end do
    zeile = ''
    do i = 1,nvmr
        read (iunit_fwd,'(A)') zeile
        read (zeile,*) hinp_m(i),(dumreal,j = 1,3),(dumreal,j = 1,ipos - 1),vmrinp(i)
    end do

    ! conversion of units
    hinp_m(1:nvmr) = 1.0d3 * hinp_m(1:nvmr) ! km to m
    vmrinp(1:nvmr) = conversion * vmrinp(1:nvmr) + konstante ! to ppm

    close (iunit_fwd)

else

    iunit_fwd = next_free_unit()
    open (iunit_fwd,file = vmrdatei,iostat = iowert,status = 'old',action = 'read')
    if (iowert .ne. 0) then
        print *,vmrdatei
        call warnout('Cannot read VMR file!',0)
    end if

    call gonext(iunit_fwd,.false.)
    read (iunit_fwd,*) nvmr
    if (nvmr .gt. nvmr_max) then
        print *,'Max levels for vmr input:',nvmr_max
        call warnout('Read_vmr: Too many levels in vmr file!',0)
    end if

    call gonext(iunit_fwd,.false.)
    read (iunit_fwd,*) (hinp_m(i),i = 1,nvmr)
    hinp_m(1:nvmr) = 1.0d3 * hinp_m(1:nvmr) ! km to m

    call gonext(iunit_fwd,.false.)
    read (iunit_fwd,*) (vmrinp(i),i=1,nvmr)

    close (iunit_fwd)

end if



flagdown = .false.

! interpolation / extrapolation of input VMR to model levels
do i = 1,n_lev
    ! downward extrapolation
    if (h_lev_m(i) .lt. hinp_m(1)) then
        vmr_lev(i) = vmrinp(1)
        if (hinp_m(1) - h_lev_m(i) .gt. 1.0d2) then
            flagdown = .true.
        end if
    else
        if (h_lev_m(i) .gt. hinp_m(nvmr)) then
            ! upward extrapolation
            vmr_lev(i) = vmrinp(nvmr)
        else
            ! interpolation
            inear = 1
            do while (hinp_m(inear+1) .lt. h_lev_m(i) .and. inear .lt. nvmr)
                inear = inear + 1
            end do
            vmr_lev(i) =vmrinp(inear) + (vmrinp(inear+1) - vmrinp(inear)) * &
              (h_lev_m(i) - hinp_m(inear)) / (hinp_m(inear+1) - hinp_m(inear))
        end if
    end if
end do

if (flagdown) then
    print *,vmrdatei
    print *,'Warning: Extrapolation in VMR at lower bound!'
end if

end subroutine read_vmr



!====================================================================
!  tofile_abscos: write precalculated abscos and solar spectrum to file
!====================================================================
subroutine tobinfile_abscos(filename,pPa_gnd,TKel_gnd,solspec &
  ,polytau,dtau_dp,dtau_dT)

use globvar24
use globlev24
use globlin24, only : n_roi,nueroi

implicit none

character(len=*),intent(in) :: filename
real(8),intent(in) :: pPa_gnd,TKel_gnd
real,dimension(wvskal%ngrid),intent(in) :: solspec
real,dimension(wvskal%ngrid,maxpoly,n_tau),intent(in) :: polytau
real,dimension(wvskal%ngrid,n_tau),intent(in) :: dtau_dp,dtau_dT

character(len = 20) :: version_info
integer :: i,j,iunit_fwd,next_free_unit

version_info = 'pcxs-2.4---rev240124'

iunit_fwd = next_free_unit()
open (iunit_fwd,file = filename,access ='stream',status = 'replace')

! version info to file
write (iunit_fwd) version_info

! all integers for array allocations
write (iunit_fwd) n_Tdisturb
write (iunit_fwd) maxpoly
write (iunit_fwd) wvskal%ngrid
write (iunit_fwd) n_tau
write (iunit_fwd) n_roi

! all floats for further aux infos
write (iunit_fwd) obs%h_m          ! real8
write (iunit_fwd) pPa_gnd          ! real8
write (iunit_fwd) TKel_gnd         ! real8
write (iunit_fwd) wvskal%firstnue  ! real8
write (iunit_fwd) wvskal%dnuerel   ! real8

! ROI regions
do i = 1,n_roi
    write (iunit_fwd) nueroi(i)  !complex8
end do

! total column of each species (real8)
do i = 1,n_tau
    write (iunit_fwd) totcol(i)
end do

! solar spectrum (real)
write (iunit_fwd) solspec(1:wvskal%ngrid)

! for each species: polytau (real),dtau_dp (real),dtau_dT (real)
do i = 1,n_tau
    do j = 1,maxpoly
        write (iunit_fwd) polytau(1:wvskal%ngrid,j,i)
    end do
    write (iunit_fwd) dtau_dp(1:wvskal%ngrid,i)
    write (iunit_fwd) dtau_dT(1:wvskal%ngrid,i)
end do

close (iunit_fwd)

end subroutine tobinfile_abscos



!====================================================================
!  tofile_AVK: write column sensitivities to file
!====================================================================
subroutine tofile_AVK(filename)

use globvar24
use globlev24

implicit none

character(len=*),intent(in) :: filename

integer :: i,j,k,l,iunit_fwd,next_free_unit

iunit_fwd = next_free_unit()
open (iunit_fwd,file = filename,status = 'replace')
do i = 1,n_tau
    do j = 1,nsens(i)
        write (iunit_fwd,'(A1)') ' '
        write (iunit_fwd,'(A8)') mw(j,i)%gasname
        write (iunit_fwd,'(A1)') '$'
        write (iunit_fwd,'(A23,30(3X,ES10.3))') &
          '          SZA[rad] ->  ',(obs%sza_gnd_rad_avk(k),k = 1,maxavk)
        write (iunit_fwd,'(A1)') ' '
        write (iunit_fwd,'(A22)') ' alt [km]     p [mbar]'
        do k = 1,n_lev
            write (iunit_fwd,'(ES10.3,30(3X,ES10.3))') 0.001d0 * lev%h_m(k),0.01d0 * lev%p_Pa(k) &
              ,(lev%colsens(k,l,j,i),l = 1,maxavk)
        end do
    end do    
end do
close (iunit_fwd)

end subroutine tofile_AVK



!====================================================================
!  tofile_lblinfos: write line pointers to file
!====================================================================
subroutine tofile_lblinfos(filename)

use globvar24
use globlin24

implicit none

character(len=*),intent(in) :: filename

integer :: i,iunit_fwd,next_free_unit

iunit_fwd = next_free_unit()
open (iunit_fwd,file = 'wrk_fast'//pathstr//filename,status = 'replace')
do i = 1,n_tau
    write (iunit_fwd,'(A150)') hitdatei(i)
    write (iunit_fwd,'(I6,1X,I6,1X,I6)') lines%lb(i),lines%rb(i),lines%rb(i) - lines%lb(i) + 1
end do
close (iunit_fwd)

end subroutine tofile_lblinfos



!====================================================================
!  tofile_pT: write p,T,n to file
!====================================================================
subroutine tofile_pT(p_lev_pa,lev_colair,T_lev_K,h_lev_m &
  ,h2o_lev_ppmv,hdo_lev_ppmv)

use globvar24, only : pathstr,sitename,yymmddchar,n_lev,datumspfad

implicit none

real(8),dimension(n_lev),intent(in) :: p_lev_pa,lev_colair,T_lev_K &
  ,h_lev_m,h2o_lev_ppmv,hdo_lev_ppmv

integer :: i,iunit_fwd,next_free_unit

iunit_fwd = next_free_unit()
open (iunit_fwd,file = 'wrk_fast'//pathstr//trim(sitename)//yymmddchar//'-pT_fast_out.dat',status = 'replace')
write (iunit_fwd,'(A)') 'Level index    Altitude(m)       Temperature(K)  ' &
  // '  Pressure(Pa)      dry air column    H2O[ppmv]         HDO[ppmv]'
do i = 1,n_lev
    write (iunit_fwd,'(I8,10(6X,ES12.5))') i,h_lev_m(i),T_lev_K(i),p_lev_pa(i) &
      ,lev_colair(i),h2o_lev_ppmv(i),hdo_lev_ppmv(i)
end do
close (iunit_fwd)

end subroutine tofile_pT



!====================================================================
!  write solar spectrum to file
!====================================================================
subroutine tofile_solspec(filename,solspec)

use globvar24

implicit none

character(len=*),intent(in) :: filename
real,dimension(wvskal%ngrid),intent(in) :: solspec

integer :: i,iunit_fwd,next_free_unit

iunit_fwd = next_free_unit()
open (iunit_fwd,file = 'wrk_fast'//pathstr//filename,status = 'replace')
do i = 1,wvskal%ngrid
    write (iunit_fwd,'(ES15.9,1X,ES12.4)') wvskal%nue(i),solspec(i)
end do
close (iunit_fwd)

end subroutine tofile_solspec



!====================================================================
!  write solar spectrum to file
!====================================================================
subroutine tofile_solspec_inp(filename,firstnue_solspec_inp,lastnue_solspec_inp,ngrid_solspec_inp,solspec_inp)

use globvar24

implicit none

character(len=*),intent(in) :: filename
integer,intent(in) :: ngrid_solspec_inp
real(8),intent(in) :: firstnue_solspec_inp,lastnue_solspec_inp 
real,dimension(ngrid_solspec_inp),intent(in) :: solspec_inp

integer :: i,iunit_fwd,next_free_unit
real(8) :: dnue

dnue = (lastnue_solspec_inp - firstnue_solspec_inp) / real(ngrid_solspec_inp - 1,8)

iunit_fwd = next_free_unit()
open (iunit_fwd,file = 'wrk_fast'//pathstr//filename,status = 'replace')
do i = 1,ngrid_solspec_inp
    write (iunit_fwd,'(ES15.9,3(1X,ES12.4))') firstnue_solspec_inp + dnue * real(i - 1,8),solspec_inp(i)
end do
close (iunit_fwd)

end subroutine tofile_solspec_inp



!====================================================================
!  write tau_lev for each species to file
!====================================================================
subroutine tofile_sumtau(filename,itau,nams,sumtau)

use globvar24

implicit none

character(len=*),intent(in) :: filename
integer,intent(in) :: itau,nams
real,dimension(wvskal%ngrid,maxams),intent(in) :: sumtau

character(2) :: exta
integer :: j,k,iunit_fwd,next_free_unit

write (exta,'(I2.2)') itau
iunit_fwd = next_free_unit()
open (iunit_fwd,file = 'wrk_fast'//pathstr//filename//exta//'.dat',status = 'replace')
do j = 1,wvskal%ngrid
    write (iunit_fwd,'(ES15.9,100(1X,ES12.4))') &
      wvskal%nue(j),(sumtau(j,k),k=1,nams)
end do
close (iunit_fwd)

end subroutine tofile_sumtau



!====================================================================
!  write tau for each species to file
!====================================================================
subroutine tofile_tau(filename,itau,tau)

use globvar24

implicit none

character(len=*),intent(in) :: filename
integer,intent(in) :: itau
real,dimension(wvskal%ngrid),intent(in) :: tau

character(2) :: exta
integer :: j,iunit_fwd,next_free_unit

write (exta,'(I2.2)') itau
iunit_fwd = next_free_unit()
open (iunit_fwd,file = 'wrk_fast'//pathstr//filename//exta//'.dat',status = 'replace')
do j = 1,wvskal%ngrid
    write (iunit_fwd,'(ES15.9,100(1X,ES12.4))') &
      wvskal%nue(j),tau(j)
end do
close (iunit_fwd)

end subroutine tofile_tau



!====================================================================
!  write tau_lev for each species to file
!====================================================================
subroutine tofile_taulev(itau,tau_lev)

use globvar24

implicit none

integer,intent(in) :: itau
real,dimension(wvskal%ngrid,n_lev),intent(in) :: tau_lev

character(2) :: exta
integer :: j,k,iunit_fwd,next_free_unit

write (exta,'(I2.2)') itau
iunit_fwd = next_free_unit()
open (iunit_fwd,file = 'wrk_fast'//pathstr//'tau_lev'//exta//'.dat',status = 'replace')
do j = 1,wvskal%ngrid
    write (iunit_fwd,'(ES15.9,100(1X,ES12.4))') wvskal%nue(j),(tau_lev(j,k),k=1,n_lev,4)
end do
close (iunit_fwd)

end subroutine tofile_taulev



!====================================================================
!  writes VMR profiles used by pcxs to file
!====================================================================
subroutine tofile_vmr(h_lev_m,vmr_ppmv)

use globvar24, only : pathstr,sitename,yymmddchar,n_lev,n_tau,datumspfad

implicit none

real(8),dimension(n_lev),intent(in) :: h_lev_m
real(8),dimension(n_lev,n_tau),intent(in) :: vmr_ppmv

integer :: i,j,iunit_fwd,next_free_unit

iunit_fwd = next_free_unit()
open (iunit_fwd,file = 'wrk_fast'//pathstr//trim(sitename)//yymmddchar//'-VMR_fast_out.dat',status = 'replace')
do i = 1,n_lev
    write (iunit_fwd,'(I4,20(6X,ES12.5))') i,h_lev_m(i),(vmr_ppmv(i,j),j = 1,n_tau)
end do
close (iunit_fwd)

end subroutine tofile_vmr



!====================================================================
!� Warnung rausschreiben und Programm evtl. beenden
!====================================================================
subroutine warnout(text,predec)

use ISO_FORTRAN_ENV, only : ERROR_UNIT
use globvar24, only : quietrundec

implicit none

character(len=*),intent(in) :: text
integer,intent(in) :: predec
character(len=1) :: chardum
integer :: intdec

print *,'Warning:'
print *, trim(text)
if (predec .eq. 0) then
    if (.not. quietrundec) then
        print *,'This is a critical error, press return for terminating exection.'
        read *,chardum
        stop
    else
        print *,'This is a critical error. Quiet run option selected: End Programm'
        write (ERROR_UNIT, *) text
        call exit(1)
    end if
else
    if (.not. quietrundec) then
        print *,'Shutdown program: enter 0 / proceed with exection: enter 1:'
        read *, intdec
        if (intdec .eq. 0) stop
    else
        print *,'Quiet run option selected, continuing execution ...'
    end if
end if

end subroutine warnout
