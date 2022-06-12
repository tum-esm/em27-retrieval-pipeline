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
! This program is for the preprocessing of COCCON measurements.
! It performs quality checks, DC-correction, FFT and phase correction,
! and a resampling of the spectrum to a minimally sampled grid.
!
! This code has been created by Frank Hase (frank.hase@kit.edu) and
! Darko Dubravica (darko.dubravica@kit.edu), both affiliated with KIT
! in the framework of ESA's COCCON-PROCEEDS project.
!
!====================================================================

program preprocess4

use glob_prepro4

implicit none

logical :: dateidadec
integer :: imeas,itest,iunit,iscan,narg,next_free_unit
character(len=200) :: inputdatei,logdatei,logdatei_test
character(len=10) :: idchar
character(len=7) :: imeaschar
character(len=4) :: argchar

character(len=lengthcharmeas),dimension(:),allocatable :: measfile
logical,dimension(:),allocatable :: dualifg
integer,dimension(:),allocatable :: nptrfirstdir,nofblock,nifg &
  ,errflag,errflag_CO,icbfwd,icbbwd,icbfwd2,icbbwd2
integer,dimension(:,:),allocatable :: blocktype,blocklength,blockptr

real(8),dimension(:),allocatable :: JDdate
real,dimension(:),allocatable :: UTh,durationsec,astrelev,azimuth

character(len=6),dimension(:),allocatable :: YYMMDDlocal,HHMMSSlocal,YYMMDDUT

real,dimension(:),allocatable :: refspec,refspec2,sinc
real,dimension(:),allocatable :: cbfwd,cbbwd,cbfwd2,cbbwd2

! arrays for processing loop
real,dimension(:),allocatable :: ifgfwd,ifgbwd,ifgfwd2,ifgbwd2
real,dimension(:),allocatable :: specfwd,specbwd,specfwd2,specbwd2
real,dimension(:),allocatable :: specfwdrs,specbwdrs,specfwd2rs,specbwd2rs
real,dimension(:),allocatable :: specmeanrs,specmean2rs
complex,dimension(:),allocatable :: cspecfwd,cspecbwd,cspecfwd2,cspecbwd2

!====================================================================
!  read command argument
!  check presence of optional tccon.inp File
!  read input file
!====================================================================
call get_command_argument(1,inputdatei)

inquire (file = 'tccon.inp',exist = dateidadec)
if (dateidadec) then
    print *,'Optional TCCON input file detected...'
    iunit = next_free_unit()
    open (iunit,file = 'tccon.inp',status = 'old',action = 'read')
    call gonext(iunit,.false.)
    read (iunit,*) TCCONkind
    print *,'TCCONkind:',TCCONkind
    close (iunit)
else
   print *,'No optional TCCON input file detected...'
   TCCONkind = 0
end if

print *,'Reading input file...'
call read_input(trim(inputdatei))
print *,'Done!'
print *,'Number of raw measurements to be processed:',nmeas

if (nmeas .gt. maxmeas) then
    print *,'nmeas maxmeas: ',nmeas,maxmeas
    call warnout ('Too many files for processing!',0)
end if

!====================================================================
!  set ifg, spectral points and OPDmax according to choice of mpowFFT
!====================================================================
select case (mpowFFT)
    case (17)
        OPDmax = 1.8d0
        ifgradius = 56873
        maxspcrs = 56874            
    case (18)
        OPDmax = 3.0d0
        ifgradius = 94788
        maxspcrs = 94789
    case default
        call warnout("Invalid choice of mpowFFT (allowed: 17 or 18)!",0)
end select
maxifg = 2**mpowFFT
maxspc = maxifg / 2 

!====================================================================
!  allocation of general arrays, init sinc, read reference spectrum (for nue cal check)
!====================================================================
allocate (dualifg(nmeas))
allocate (measfile(nmeas),nptrfirstdir(nmeas),nofblock(nmeas) &
  ,nifg(nmeas),errflag(nmeas),errflag_CO(nmeas))
allocate (icbfwd(nmeas),icbbwd(nmeas),icbfwd2(nmeas),icbbwd2(nmeas))
allocate (cbfwd(nmeas),cbbwd(nmeas),cbfwd2(nmeas),cbbwd2(nmeas))
allocate (blocktype(maxblock,nmeas),blocklength(maxblock,nmeas),blockptr(maxblock,nmeas))
allocate (YYMMDDlocal(nmeas),HHMMSSlocal(nmeas),YYMMDDUT(nmeas))
allocate (JDdate(nmeas),UTh(nmeas),durationsec(nmeas),astrelev(nmeas),azimuth(nmeas))
nsinc = nzf * nconv
allocate (sinc(-nsinc:nsinc))
allocate (refspec(maxspc),refspec2(maxspc))

call prepare_sinc(sinc)

if (checkoutdec) then 
    call tofile_spec(trim(diagoutpath)//pathstr//'sinc.dat',2*nsinc+1,sinc(-nsinc:nsinc))
end if

call read_refspec('refspec.dat',maxspc,refspec)
call read_refspec('refspec2.dat',maxspc,refspec2)

!====================================================================
!  read file names
!====================================================================
print *,'Reading file names'
call read_meas_files(trim(inputdatei),nmeas,measfile)
print *,'Done!'

!====================================================================
!  read all OPUS file headers, ephemerid calculation
!====================================================================
errflag(1:nmeas) = 0
errflag_CO(1:nmeas) = 0

do imeas = 1,nmeas

    print *,'Read OPUS parms:',imeas

    ! read OPUS parms
    call read_opus_hdr(measfile(imeas),nptrfirstdir(imeas),nofblock(imeas))
    call read_opus_dir(measfile(imeas),nptrfirstdir(imeas),nofblock(imeas) &
      ,blocktype(1:maxblock,imeas),blocklength(1:maxblock,imeas) &
      ,blockptr(1:maxblock,imeas),dualifg(imeas),nifg(imeas))
    call read_opus_parms(imeas,measfile(imeas),nofblock(imeas) &
      ,blocktype(1:maxblock,imeas),blocklength(1:maxblock,imeas),blockptr(1:maxblock,imeas))

    ! check formal consistency of file with COCCON / preprocessor demands
    call checkOPUSparms(measfile(imeas),imeas)

end do




do imeas = 1,nmeas
    ! calculate solar position
    call calcsolpos(imeas,JDdate(imeas),YYMMDDlocal(imeas),HHMMSSlocal(imeas),YYMMDDUT(imeas),UTh(imeas) &
      ,durationsec(imeas),astrelev(imeas),azimuth(imeas))
    ! set error flag if astronomical (solar elevation below 1 deg)
    if (astrelev(imeas) .lt. 1.0) then
        errflag(imeas) = errflag(imeas) + 1
        errflag_CO(imeas) = errflag_CO(imeas) + 1
    end if     
end do

! allocate interferogram and spectrum workspace for processing loop
allocate (ifgfwd(maxifg),ifgbwd(maxifg),ifgfwd2(maxifg),ifgbwd2(maxifg))
allocate (cspecfwd(maxspc),cspecbwd(maxspc),cspecfwd2(maxspc),cspecbwd2(maxspc))
allocate (specfwd(maxspc),specbwd(maxspc),specfwd2(maxspc),specbwd2(maxspc))
allocate (specfwdrs(maxspcrs),specbwdrs(maxspcrs),specfwd2rs(maxspcrs),specbwd2rs(maxspcrs))
allocate (specmeanrs(maxspcrs),specmean2rs(maxspcrs))

if (binoutpath(1:8) .eq. 'standard') then
    iscan = scan(measfile(1),pathstr,.true.)
    logdatei = measfile(1)(1:iscan-1)//pathstr//'cal'//pathstr//'logfile.dat'
    logdatei_test = logdatei
else
    logdatei = trim(binoutpath)//pathstr//'logfile.dat'
    logdatei_test = ''
end if
iunit = next_free_unit()
open (iunit,file = logdatei,status = 'replace')
close (iunit)

!====================================================================
!  process all raw interferograms
!====================================================================

do imeas = 1,nmeas

    if (binoutpath(1:8) .eq. 'standard') then
        iscan = scan(measfile(imeas),pathstr,.true.)
        logdatei_test = measfile(imeas)(1:iscan-1)//pathstr//'cal'//pathstr//'logfile.dat'
        if (logdatei_test .ne. logdatei) then
            logdatei = logdatei_test
            iunit = next_free_unit()
            open (iunit,file = logdatei,status = 'replace')
            close (iunit)
        end if
    end if

    print *,'Starting preprocessing loop for spectrum:',imeas

    write (imeaschar,'(I7.7)') imeas
    idchar = imeaschar
    
    
    print *,'Reading file from disc ...',imeas

    ! read OPUS file
    call read_ifg(nofblock(imeas),nifg(imeas),dualifg(imeas),measfile(imeas) &
      ,blocktype(1:maxblock,imeas),blockptr(1:maxblock,imeas),ifgfwd &
      ,ifgbwd,ifgfwd2,ifgbwd2)

    if (TCCONkind .eq. 1) then
            dualifg(imeas) = .true.
            ifgfwd2 = ifgfwd
            ifgbwd2 = ifgbwd
    end if
    
    if (checkoutdec) then
        call tofile_ifg(trim(diagoutpath)//pathstr//'ifgfwd_'//idchar//'.dat',nifg(imeas),ifgfwd)
        call tofile_ifg(trim(diagoutpath)//pathstr//'ifgbwd_'//idchar//'.dat',nifg(imeas),ifgbwd)

        if (dualifg(imeas)) then
            call tofile_ifg(trim(diagoutpath)//pathstr//'ifgfwd2_'//idchar//'.dat',nifg(imeas),ifgfwd2)
            call tofile_ifg(trim(diagoutpath)//pathstr//'ifgbwd2_'//idchar//'.dat',nifg(imeas),ifgbwd2)    
        end if
    end if

    print *,'DC correction ...',imeas
    
    ! perform DC correction
    call DCtoACifg(DCmin,DCvar,nifg(imeas),errflag(imeas),icbfwd(imeas),cbfwd(imeas),ifgfwd)
    call DCtoACifg(DCmin,DCvar,nifg(imeas),errflag(imeas),icbbwd(imeas),cbbwd(imeas),ifgbwd)
    if (errflag(imeas) .eq. 0) then
        if ((cbfwd(imeas) - cbbwd(imeas)) / (cbfwd(imeas) + cbbwd(imeas)) .gt. 0.1) &
          errflag(imeas) = errflag(imeas) + 1000
    end if
    if (dualifg(imeas) .and. errflag(imeas) .eq. 0) then
        call DCtoACifg(DCmin,DCvar,nifg(imeas),errflag_CO(imeas),icbfwd2(imeas),cbfwd2(imeas),ifgfwd2)
        call DCtoACifg(DCmin,DCvar,nifg(imeas),errflag_CO(imeas),icbbwd2(imeas),cbbwd2(imeas),ifgbwd2)
        if (errflag_CO(imeas) .eq. 0) then
            if ((cbfwd(imeas) - cbbwd(imeas)) / (cbfwd(imeas) + cbbwd(imeas)) .gt. 0.1) &
              errflag_CO(imeas) = errflag_CO(imeas) + 1000
        end if
    end if

    if (checkoutdec) then
        call tofile_ifg(trim(diagoutpath)//pathstr//'ifgfwdsm_'//idchar//'.dat',nifg(imeas),ifgfwd)
        call tofile_ifg(trim(diagoutpath)//pathstr//'ifgbwdsm_'//idchar//'.dat',nifg(imeas),ifgbwd)
        if (dualifg(imeas)) then
            call tofile_ifg(trim(diagoutpath)//pathstr//'ifgfwdsm2_'//idchar//'.dat',nifg(imeas),ifgfwd2)
            call tofile_ifg(trim(diagoutpath)//pathstr//'ifgbwdsm2_'//idchar//'.dat',nifg(imeas),ifgbwd2)
        end if
    end if

    print *,'Preparing FFT ...',imeas

    ! apodization and clipping to 1.8 cm OPDmax, check whether DS FFT can be performed
    if (errflag(imeas) .eq. 0) then
        call APOifg(nifg(imeas),icbfwd(imeas),errflag(imeas),ifgfwd)
        call APOifg(nifg(imeas),icbbwd(imeas),errflag(imeas),ifgbwd)
        if (dualifg(imeas) .and. errflag_CO(imeas) .eq. 0) then
            call APOifg(nifg(imeas),icbfwd2(imeas),errflag_CO(imeas),ifgfwd2)
            call APOifg(nifg(imeas),icbbwd2(imeas),errflag_CO(imeas),ifgbwd2)
        end if
 
        if (checkoutdec) then
            call tofile_ifg(trim(diagoutpath)//pathstr//'ifgfwdapo_'//idchar//'.dat',maxifg,ifgfwd)
            call tofile_ifg(trim(diagoutpath)//pathstr//'ifgbwdapo_'//idchar//'.dat',maxifg,ifgbwd)
            if (dualifg(imeas)) then
                call tofile_ifg(trim(diagoutpath)//pathstr//'ifgfwdapo2_'//idchar//'.dat',maxifg,ifgfwd2)
                call tofile_ifg(trim(diagoutpath)//pathstr//'ifgbwdapo2_'//idchar//'.dat',maxifg,ifgbwd2)
            end if
        end if
    end if

    print *,'FFT ...',imeas

    ! perform FFT
    if (errflag(imeas) .eq. 0) then
        call FFT(ifgfwd,cspecfwd)
        call FFT(ifgbwd,cspecbwd)
        if (dualifg(imeas) .and. errflag_CO(imeas) .eq. 0) then
            call FFT(ifgfwd2,cspecfwd2)
            call FFT(ifgbwd2,cspecbwd2)
        end if
    
        if (checkoutdec) then
            call tofile_cspec(trim(diagoutpath)//pathstr//'cspecfwd_'//idchar//'.dat',maxspc,cspecfwd)
            call tofile_cspec(trim(diagoutpath)//pathstr//'cspecbwd_'//idchar//'.dat',maxspc,cspecbwd)
            if (dualifg(imeas)) then
                call tofile_cspec(trim(diagoutpath)//pathstr//'cspecfwd2_'//idchar//'.dat',maxspc,cspecfwd2)
                call tofile_cspec(trim(diagoutpath)//pathstr//'cspecbwd2_'//idchar//'.dat',maxspc,cspecbwd2)
            end if
        end if
    end if

    ! check out-of-band artefacts   
    if (errflag(imeas) .eq. 0 .and. TCCONkind .eq. 0) then
        call checkoutofband(1,errflag(imeas),cspecfwd,cspecbwd)
        if (dualifg(imeas) .and. errflag_CO(imeas) .eq. 0) then
            call checkoutofband(2,errflag_CO(imeas),cspecfwd2,cspecbwd2)
        end if
    end if

    print *,'Phase correction ...',imeas

    ! perform phase correction
    if (errflag(imeas) .eq. 0) then
        call phasecorr(1,errflag(imeas),cspecfwd,specfwd)
        call phasecorr(1,errflag(imeas),cspecbwd,specbwd)
        if (dualifg(imeas) .and. errflag_CO(imeas) .eq. 0) then
            call phasecorr(2,errflag_CO(imeas),cspecfwd2,specfwd2)
            call phasecorr(2,errflag_CO(imeas),cspecbwd2,specbwd2)
        end if

        if (checkoutdec) then
            call tofile_spec(trim(diagoutpath)//pathstr//'specfwd_'//idchar//'.dat',maxspc,specfwd)
            call tofile_spec(trim(diagoutpath)//pathstr//'specbwd_'//idchar//'.dat',maxspc,specbwd)
            if (dualifg(imeas)) then
                call tofile_spec(trim(diagoutpath)//pathstr//'specfwd2_'//idchar//'.dat',maxspc,specfwd2)
                call tofile_spec(trim(diagoutpath)//pathstr//'specbwd2_'//idchar//'.dat',maxspc,specbwd2)
            end if
        end if
    end if

    ! check spectral calibration
    if (errflag(imeas) .eq. 0) then
        call checknuecal(1,errflag(imeas),refspec,specfwd)
        call checknuecal(1,errflag(imeas),refspec,specbwd)
        if (dualifg(imeas) .and. errflag_CO(imeas) .eq. 0) then
            call checknuecal(2,errflag_CO(imeas),refspec2,specfwd2)
            call checknuecal(2,errflag_CO(imeas),refspec2,specbwd2)
        end if
    end if

    ! check consistency of fwd and bwd pair of spectra
    if (errflag(imeas) .eq. 0) then
        call checkfwdbwd(1,errflag(imeas),specfwd,specbwd)
        if (dualifg(imeas) .and. errflag_CO(imeas) .eq. 0) then
            call checkfwdbwd(2,errflag_CO(imeas),specfwd2,specbwd2)
        end if    
    end if

    ! apply a slight additional self-apodisation on TCCON spectra for matching EM27/SUN
    if (TCCONkind .gt. 0) then
        call smoothspec(maxspc,specfwd)
        call smoothspec(maxspc,specbwd)
        call smoothspec(maxspc,specfwd2)
        call smoothspec(maxspc,specbwd2)
    end if

    print *,'Spectral resampling ...',imeas

    ! perform spectral resampling, file to disc
    if (errflag(imeas) .eq. 0) then
        call resample(1,sinc,specfwd,specfwdrs)
        call resample(1,sinc,specbwd,specbwdrs)
        if (dualifg(imeas) .and. errflag_CO(imeas) .eq. 0) then
            call resample(2,sinc,specfwd2,specfwd2rs)
            call resample(2,sinc,specbwd2,specbwd2rs)
        end if

        if (checkoutdec) then
            call tofile_spec(trim(diagoutpath)//pathstr//'specfwdrs_'//idchar//'.dat',maxspcrs,specfwdrs)
            call tofile_spec(trim(diagoutpath)//pathstr//'specbwdrs_'//idchar//'.dat',maxspcrs,specbwdrs)
            if (dualifg(imeas)) then
                call tofile_spec(trim(diagoutpath)//pathstr//'specfwd2rs_'//idchar//'.dat',maxspcrs,specfwd2rs)
                call tofile_spec(trim(diagoutpath)//pathstr//'specbwd2rs_'//idchar//'.dat',maxspcrs,specbwd2rs)
            end if
        end if
    end if    

    ! average fwd+bwd, write bin-file to disc
    if (errflag(imeas) .eq. 0) then
        print *,'Binary file(s) to disc ...',imeas
        specmeanrs = 0.5 * (specfwdrs + specbwdrs)
        call tofile_binspec(1,measfile(imeas),YYMMDDlocal(imeas),HHMMSSlocal(imeas),YYMMDDUT(imeas) &
          ,UTh(imeas),durationsec(imeas),astrelev(imeas),azimuth(imeas),specmeanrs)
        if (dualifg(imeas) .and. errflag_CO(imeas) .eq. 0) then
            specmean2rs = 0.5 * (specfwd2rs + specbwd2rs)
            call tofile_binspec(2,measfile(imeas),YYMMDDlocal(imeas),HHMMSSlocal(imeas),YYMMDDUT(imeas) &
              ,UTh(imeas),durationsec(imeas),astrelev(imeas),azimuth(imeas),specmean2rs)
        end if
    else
        print *,'errflag:',errflag(imeas)
        if (dualifg(imeas)) print *,'errflag_CO:',errflag_CO(imeas)
    end if

    iunit = next_free_unit()
    open (iunit,file = logdatei,status = 'old',position = 'append')
    write (iunit,'(I7,2X,I9,2X,I8,2X,F9.5,2X,F9.4,2X,F9.4,2X,A6,2X,A6,2X,A6,2X,A)') imeas,errflag(imeas) &
      ,errflag_CO(imeas),astrelev(imeas),azimuth(imeas),UTh(imeas),YYMMDDUT(imeas),YYMMDDlocal(imeas),HHMMSSlocal(imeas) &
      ,trim(measfile(imeas))
    close (iunit)

end do

! deallocate arrays of parallel loop
deallocate (specmeanrs,specmean2rs)
deallocate (specfwdrs,specbwdrs,specfwd2rs,specbwd2rs)
deallocate (specfwd,specbwd,specfwd2,specbwd2)
deallocate (cspecfwd,cspecbwd,cspecfwd2,cspecbwd2)
deallocate (ifgfwd,ifgbwd,ifgfwd2,ifgbwd2)

!====================================================================
!  Deallocation of general arrays
!====================================================================
deallocate (refspec,refspec2)
deallocate (sinc)

deallocate (JDdate,UTh,durationsec,astrelev,azimuth)
deallocate (YYMMDDlocal,HHMMSSlocal,YYMMDDUT)
deallocate (cbfwd,cbbwd,cbfwd2,cbbwd2)
deallocate (blocktype,blocklength,blockptr)
deallocate (measfile,nptrfirstdir,nofblock,nifg)
deallocate (errflag,errflag_CO,icbfwd,icbbwd,icbfwd2,icbbwd2)
deallocate (dualifg)

end program preprocess4











!====================================================================
!  APOifg
!====================================================================
subroutine APOifg(nifg,icb,errflag,ifg)

use glob_prepro4,only : maxifg,ifgradius

implicit none

integer,intent(in) :: nifg,icb
integer,intent(inout) :: errflag
real,dimension(maxifg),intent(inout) :: ifg

integer :: i
real :: xwert,term,apowert
real,dimension(:), allocatable :: wrkifg

if ((icb - ifgradius) .lt. 1 .or. (icb + ifgradius) .gt. nifg) then
    errflag = errflag + 10000
    call warnout("IFG centerburst is decentered!",1)
    return
end if

allocate (wrkifg(maxifg))
wrkifg = ifg
ifg = 0.0

! set to zero outside OPDmax
do i = 1,icb - ifgradius - 1
    wrkifg(i) = 0.0
end do
do i = icb + ifgradius + 1,maxifg
    wrkifg(i) = 0.0
end do

! NBM apodization
do i = 1,ifgradius
    xwert = real(i) / real(ifgradius)
    term = (1.0 - xwert * xwert)
    apowert = 0.152442 - 0.136176 * term + 0.983734 * term * term
    wrkifg(icb-i) = wrkifg(icb-i) * apowert
    wrkifg(icb+i) = wrkifg(icb+i) * apowert
end do

! resort array for FFT
ifg(1) = wrkifg(icb)
do i = 1,ifgradius
    ifg(i+1) = wrkifg(icb-i)
end do
do i = 1,ifgradius
    ifg(maxifg-i+1) = wrkifg(icb+i)
end do

deallocate (wrkifg)

end subroutine APOifg



!====================================================================
!  calcsolpos
!====================================================================
subroutine calcsolpos(imeas,JDdate,YYMMDDlocal,HHMMSSlocal,YYMMDDUT,UTh,durationsec,astrelevdeg,azimuthdeg)

use glob_prepro4, only : gradtorad,radtograd,obsfixlatdeg,obsfixlondeg,toffseth_UT
use glob_OPUSparms

implicit none

integer,intent(in) :: imeas
real(8),intent(out) :: JDdate
character(len=6),intent(out) :: YYMMDDlocal,HHMMSSlocal,YYMMDDUT
real,intent(out) :: UTh,durationsec,astrelevdeg,azimuthdeg

character(len=2) :: YY,MM,DD
integer :: iscan,hours,minutes,ijahr,imonat,itag
real :: velocity,seconds
real(8) :: JDcorr,arrad,decrad,laengerad,breiterad,azimutrad,hoeherad

! derive local YYMMDD from OPUS parameter (reported date in *.bin-File)
iscan = scan(OPUS_parms(imeas)%DAT,'/')
YYMMDDlocal = OPUS_parms(imeas)%DAT(iscan+6:iscan+7)//OPUS_parms(imeas)%DAT(iscan+1:iscan+2) &
  // OPUS_parms(imeas)%DAT(iscan-2:iscan-1)

! derive HHMMSSlocal from OPUS parameters (start time used for file naming)
iscan = scan(OPUS_parms(imeas)%TIM,':')
HHMMSSlocal = OPUS_parms(imeas)%TIM(iscan-2:iscan-1)//OPUS_parms(imeas)%TIM(iscan+1:iscan+2) &
  // OPUS_parms(imeas)%TIM(iscan+4:iscan+5)

read(OPUS_parms(imeas)%TIM(iscan-2:iscan-1),*) hours
read(OPUS_parms(imeas)%TIM(iscan+1:iscan+2),*) minutes
read(OPUS_parms(imeas)%TIM(iscan+4:iscan+8),*) seconds

! derive UT time from OPUS parameter, duration of measurement and optional time correction
! determine scan duration
read(OPUS_parms(imeas)%VEL,*) velocity
durationsec = 58.32 / velocity * real(OPUS_parms(imeas)%NSS)

! derive UT time from OPUS time and toffseth_UT
UTh = real(hours) - toffseth_UT + real(minutes) / 60.0 + (seconds + 0.5 * durationsec) / 3600.0

JDcorr = 0.0d0
if (UTh .lt. 0.0) then
    UTh = UTh + 24.0
    JDcorr = -1.0d0
end if
if (UTh .gt. 24.0) then
    UTh = UTh - 24.0
    JDcorr = 1.0d0
end if

JDdate = JD(YYMMDDlocal,UTh) + JDcorr

call JDinv(JDdate,ijahr,imonat,itag)

write (YY,'(I2.2)') ijahr - 2000
write (MM,'(I2.2)') imonat
write (DD,'(I2.2)') itag
YYMMDDUT = YY//MM//DD

! determine solar position
call sunpos (JDdate,arrad,decrad)
laengerad = -gradtorad * obsfixlondeg
breiterad = gradtorad * obsfixlatdeg
call horizkoords(JDdate,laengerad,breiterad,arrad,decrad,azimutrad,hoeherad)
astrelevdeg = radtograd * hoeherad
azimuthdeg = radtograd * azimutrad


contains

    !====================================================================
    !  JD
    !====================================================================
    real(8) function JD(YYMMDD,UTh)

    implicit none

    character(len=6),intent(in) :: YYMMDD
    real,intent(in) :: UTh

    integer :: jahr,monat,itag,werta,wertb
    real(8) :: ftag

    read (YYMMDD(1:2),*) jahr
    jahr = jahr + 2000
    read (YYMMDD(3:4),*) monat
    read (YYMMDD(5:6),*) itag

    ftag = real(itag,8) + real(UTh,8) / 24.0d0

    if (monat .eq. 1 .or. monat .eq. 2) then
        jahr = jahr - 1
        monat = monat + 12
    end if

    werta = int(0.01d0 * real(jahr,8))
    wertb = 2 - werta + int(0.25d0 * real(werta,8))

    JD = int(365.25d0 * real(jahr + 4716,8)) &
      + int(30.6001d0 * real(monat + 1,8)) + ftag + real(wertb,8) - 1524.5d0

    end function JD



    !====================================================================
    !  JDinv
    !====================================================================
    subroutine JDinv(jdwert,ijahr,imonat,itag)

    implicit none

    real(8),intent(in) :: jdwert
    integer,intent(out) :: ijahr,imonat,itag

    real(8) :: jdwrk,f
    integer :: alpha,z,a,b,c,d,e

    jdwrk = jdwert + 0.5d0

    z = int(jdwrk)
    f = jdwrk - real(z,8)

    if (real(z,8) .lt. 2299161.0d0) then
        a = z
    else
        alpha = int((real(z,8) - 1867216.25d0) / 36524.25d0)
        a = z + 1 + alpha - int(0.25d0 * real(alpha,8))
    end if

    b = a + 1524
    c = int((real(b,8) - 122.1d0) / 365.25d0)
    d = int(365.25d0 * real(c,8))
    e = int(real(b - d,8) / 30.6001d0)

    itag = b - d - int(30.6001d0 * real(e,8))! Tag

    imonat = -99
    if (e .lt. 14) then ! Monat
        imonat = e - 1
    else
        if (e .eq. 14 .or. e .eq. 15) then
            imonat = e - 13
        end if
    end if

    ijahr = - 9999
    if (imonat .gt. 2) then
        ijahr = c - 4716
    else
        if (imonat .eq. 1 .or. imonat .eq. 2) then
            ijahr = c - 4715
        end if
    end if

    end subroutine JDinv



    !====================================================================
    !  sub horizkoords
    !====================================================================
    subroutine horizkoords(jdwert,laengerad,breiterad,arrad,decrad &
      ,azimutrad,hoeherad)    

    implicit none

    real(8), intent(in) :: jdwert
    real(8),intent(in) :: laengerad,breiterad,arrad,decrad
    real(8),intent(out) :: azimutrad,hoeherad

    real(8) :: hwinkel

    hwinkel = sideralgw (jdwert) - laengerad - arrad
    azimutrad = atan2(sin(hwinkel),cos(hwinkel) * sin(breiterad) &
      - tan(decrad) * cos(breiterad))
    hoeherad = asin(sin(breiterad) * sin(decrad) + cos(breiterad) &
      * cos(decrad) * cos(hwinkel))

    end subroutine horizkoords



    !====================================================================
    !  function schieferad
    !====================================================================
    real(8) function schieferad (jdwert)

    implicit none

    real(8),intent(in) :: jdwert

    real(8) :: t

    t = (jdwert - 2451545.0d0) / 36525.0d0
    schieferad = 0.409092804d0 - 2.2696552d-4 * t - 2.8604d-9 * t * t &
      - 8.789672d-9 * t * t * t

    end function



    !====================================================================
    !  function sideralgw
    !====================================================================
    real(8) function sideralgw (jdwert)

    use glob_prepro4, only : gradtorad

    implicit none

    real(8),intent(in) :: jdwert

    real(8) :: t,wert

    t = (jdwert - 2451545.0d0) / 36525.0d0
    wert = 280.46061837d0 + 360.98564736629d0 * &
      (jdwert - 2451545.0d0) + 3.87933d-4 * t * t - 2.5833118d-8 * &
      t * t * t
    sideralgw = gradtorad * modulo(wert,360.0d0)

    end function sideralgw



    !====================================================================
    !  subroutine sunpos
    !====================================================================
    subroutine sunpos(jdwert,arrad,decrad)

    use glob_prepro4, only : gradtorad

    implicit none

    real(8),intent(in) :: jdwert
    real(8),intent(out) :: arrad,decrad

    real(8) :: t,lnull,m,mrad,cwert,slong,slongrad,schiefe,jdecorr

    jdecorr = 7.176d-4 + 1.459d-8 * (jdwert - 2451545.0d0) 
    t = (jdwert - jdecorr - 2451545.0d0) / 36525.0d0

    lnull = 280.46645d0 + 36000.76983d0 * t + 0.0003032d0 * t * t
    lnull = modulo(lnull,360.0d0)

    m = 357.52910d0 + 35999.05030d0 * t - 0.0001559d0 * t * t &
     - 4.8d-7 * t * t * t
    m = modulo(m,360.0d0)
    mrad = gradtorad * m

    cwert = (1.9146d0 - 4.817d-3 * t - 1.4d-5 * t * t) * sin(mrad) &
      + (1.9993d-2 - 1.01d-4 * t) * sin(2.0d0 * mrad) + 2.9d-4 * &
      sin(3.0d0 * mrad)

    slong = lnull + cwert
    slongrad = gradtorad * slong

    schiefe = schieferad(jdwert)
    arrad = atan2(cos(schiefe) * sin(slongrad),cos(slongrad))
    decrad = asin(sin(schiefe) * sin(slongrad))

    end subroutine sunpos



end subroutine calcsolpos



!====================================================================
!  checkfwdbwd
!====================================================================
subroutine checkfwdbwd(ichan,errflag,specfwd,specbwd)

use glob_prepro4,only : maxspc,nuelas

implicit none

integer,intent(in) :: ichan
integer,intent(inout) :: errflag
real,dimension(maxspc),intent(in) :: specfwd,specbwd

real(8),parameter :: nuesiglow1 = 5544.0d0
real(8),parameter :: nuesighigh1 = 12053.0d0
real(8),parameter :: nuesiglow2 = 4098.0d0
real(8),parameter :: nuesighigh2 = 5062.0d0
real(8),parameter :: schwelle1 = 0.001d0
real(8),parameter :: schwelle2 = 0.001d0

integer :: i,isiglow,isighigh
real :: ratio
real(8) :: dnuefft,diffwert,sigfwd,sigbwd

dnuefft = nuelas / real(maxspc - 1,8)

if (ichan .eq. 1) then
    isiglow = nuesiglow1 / dnuefft
    isighigh = nuesighigh1 / dnuefft
else
    isiglow = nuesiglow2 / dnuefft
    isighigh = nuesighigh2 / dnuefft
end if

sigfwd = 0.0d0
sigbwd = 0.0d0
do i = isiglow,isighigh
    sigfwd = sigfwd + specfwd(i)
    sigbwd = sigbwd + specbwd(i)
end do
ratio = sigfwd / sigbwd

diffwert = 0.0d0
do i = isiglow,isighigh
    diffwert = diffwert + 2.0 * abs((specfwd(i) - ratio * specbwd(i)) / (sigfwd + sigbwd))
end do
diffwert = diffwert / real(isighigh - isiglow + 1,8)

!print *,ichan,diffwert
if (ichan .eq. 1) then
    if (diffwert .gt. schwelle1) errflag = errflag + 100000000
else
    if (diffwert .gt. schwelle2) errflag = errflag + 100000000
end if

end subroutine checkfwdbwd



!====================================================================
!  checknuecal
!====================================================================
subroutine checknuecal(ichan,errflag,refspec,spec)

use glob_prepro4,only : maxspc,nuelas

implicit none

integer,intent(in) :: ichan
integer,intent(inout) :: errflag
real,dimension(maxspc) :: refspec,spec

integer,parameter :: ishiftmax = 2
real(8),parameter :: nueminix1 = 7835.0d0
real(8),parameter :: nuemaxix1 = 7979.0d0
real(8),parameter :: nueminix2 = 4809.0d0
real(8),parameter :: nuemaxix2 = 4886.0d0

integer :: ishift,ix,minix,maxix,ishift_maxcorr
real(8) :: dnuefft,actcorrel,maxcorrel
real,dimension(-ishiftmax:ishiftmax) :: correl

dnuefft = nuelas / real(maxspc - 1,8)

if (ichan .eq. 1) then
    minix = nueminix1 / dnuefft
    maxix = nuemaxix1 / dnuefft
else
    minix = nueminix2 / dnuefft
    maxix = nuemaxix2 / dnuefft
end if

maxcorrel = 0.0d0
do ishift = -ishiftmax,ishiftmax
    actcorrel = 0.0d0
    do ix = minix,maxix
        actcorrel = actcorrel + (refspec(ix+1) - 2.0 * refspec(ix) + refspec(ix-1)) &
          * (spec(ix+1+ishift) - 2.0 * spec(ix+ishift) + spec(ix-1+ishift))
    end do
    correl(ishift) = actcorrel
    if (maxcorrel .lt. actcorrel) then
        maxcorrel = actcorrel
        ishift_maxcorr = ishift
    end if
    !print *,ishift,correl(ishift)
end do

if (abs(ishift_maxcorr) .eq. ishiftmax) then
    errflag = errflag + 10000000
end if

end subroutine checknuecal



!====================================================================
!  checkOPUSparms
!====================================================================
subroutine checkOPUSparms(measfile,imeas)

use glob_prepro4, only : OPDmax
use glob_OPUSparms

implicit none

character(len=*),intent(in) :: measfile
integer,intent(in) :: imeas

if (OPUS_parms(imeas)%RES .lt. 0.8999999d0 / OPDmax) then
    print *,measfile
    print *,'OPUS RES:',OPUS_parms(imeas)%RES
    print *,'Requested RES:',0.9d0 / OPDmax
    call warnout ('RES too small!',0)
end if

if (modulo(OPUS_parms(imeas)%NSS,2) .gt. 0) then
    print *,measfile
    call warnout ('Uneven number of scans!',0)    
end if

if (scan(OPUS_parms(imeas)%AQM,"DD") .lt. 1) then
    print *,measfile
    call warnout ('IFG not double-sided!',0)
end if

end subroutine checkOPUSparms



!====================================================================
!  checkoutofband
!====================================================================
subroutine checkoutofband(ichan,errflag,cspecfwd,cspecbwd)

use glob_prepro4,only : maxspc,nuelas

implicit none

integer,intent(in) :: ichan
integer,intent(inout) :: errflag
complex,dimension(maxspc) :: cspecfwd,cspecbwd

real(8),parameter :: nuesiglow1 = 5544.0d0
real(8),parameter :: nuesighigh1 = 12535.0d0
real(8),parameter :: nueofflow1 = 964.0d0
real(8),parameter :: nueoffhigh1 = 4339.0d0
real(8),parameter :: schwelle1 = 0.005

real(8),parameter :: nuesiglow2 = 4098.0d0
real(8),parameter :: nuesighigh2 = 5062.0d0
real(8),parameter :: nueofflow2 = 6268.0d0
real(8),parameter :: nueoffhigh2 = 15669.0d0
real(8),parameter :: schwelle2 = 0.01

integer :: i,isiglow,isighigh,iofflow,ioffhigh
real(8) :: dnuefft,signal,schwelle,artefact

dnuefft = nuelas / real(maxspc - 1,8)

if (ichan .eq. 1) then
    isiglow = nuesiglow1 / dnuefft
    isighigh = nuesighigh1 / dnuefft
    iofflow = nueofflow1 / dnuefft
    ioffhigh = nueoffhigh1 / dnuefft
    schwelle = schwelle1
else
    isiglow = nuesiglow2 / dnuefft
    isighigh = nuesighigh2 / dnuefft
    iofflow = nueofflow2 / dnuefft
    ioffhigh = nueoffhigh2 / dnuefft
    schwelle = schwelle2
end if

signal = 0.0d0
artefact = 0.0d0
do i = isiglow,isighigh
    signal = signal + abs(cspecfwd(i)) + abs(cspecbwd(i))
end do
signal = signal / real(isighigh - isiglow + 1,8)
do i = iofflow,ioffhigh
    artefact = artefact + abs(cspecfwd(i)) + abs(cspecbwd(i))
end do
artefact = artefact / real(ioffhigh - iofflow + 1,8)
!print *,ichan,artefact / signal
if (artefact / signal .gt. schwelle) then
    errflag = errflag + 100000
end if

end subroutine checkoutofband



!====================================================================
!  DCtoACifg
!====================================================================
subroutine DCtoACifg(DCmin,DCvar,nifg,errflag,icb,cbamp,ifg)

use glob_prepro4,only : maxifg,nsmooth

implicit none

real,intent(in) :: DCmin,DCvar
integer,intent(in) :: nifg
integer,intent(inout) :: errflag
integer,intent(out) :: icb
real,intent(out) :: cbamp
real,dimension(maxifg),intent(inout) :: ifg

integer :: i,ismooth
real :: werta,wertb,abswert,minwert,maxwert,mean,var
real,dimension(:),allocatable :: wrkifg

allocate(wrkifg(maxifg))

wrkifg = ifg
do ismooth = 1,nsmooth
    werta = 0.5 * (wrkifg(1) + wrkifg(2))
    do i = 2,nifg - 1
        wertb = 0.25 * wrkifg(i-1) + 0.5 * wrkifg(i) + 0.25 * wrkifg(i+1)
        wrkifg(i-1) = werta
        werta = wertb
    end do
    wrkifg(nifg) = 0.5 * (wrkifg(nifg-1) + wrkifg(nifg))
    wrkifg(nifg-1) = werta
end do

! Check DC level and variation
mean = 0.0
minwert = wrkifg(1)
maxwert = wrkifg(1)
do i = 1,nifg
    mean = mean + wrkifg(i)
    if (abs(wrkifg(i)) .lt. abs(minwert)) minwert = wrkifg(i)
    if (abs(wrkifg(i)) .gt. abs(maxwert)) maxwert = wrkifg(i)
end do
mean = mean / real(nifg)
var = maxwert / minwert - 1.0

if (abs(mean) .lt. DCmin) then
    errflag = errflag + 10
    deallocate(wrkifg)
    return
end if

if (abs(var) .gt. DCvar) then
    errflag = errflag + 100
    deallocate(wrkifg)
    return
end if

abswert = 0.0
do i = 1,nifg
    ifg(i) = mean * (ifg(i) / wrkifg(i) - 1.0)
    if (abs(ifg(i)) .gt. abswert) then
        abswert = abs(ifg(i))
        icb = i
    end if
end do

minwert = minval(ifg(1:nifg))
maxwert = maxval(ifg(1:nifg))

cbamp = abs(maxwert - minwert)

deallocate(wrkifg)

end subroutine DCtoACifg



!====================================================================
!  FFT
!====================================================================
subroutine FFT(ifg,spec)

use glob_prepro4,only : mpowFFT,maxifg,maxspc,pi

implicit none

real,dimension(maxifg),intent(in) :: ifg
complex,dimension(maxspc),intent(out) :: spec

integer :: i,j,k,l,n1,n2
real(8) :: angle,argument,xdum,ydum,c,s
real(8),dimension(:),allocatable :: x,y

allocate(x(maxifg),y(maxifg))

do i = 1,maxifg
    x(i) = real(ifg(i),8)
end do
y = 0.0d0

n2 = maxifg
do k = 1,mpowFFT
    n1 = n2
    n2 = n2 / 2
    angle = 0.0d0
    argument = 2.0d0 * pi / real(n1,8)
    do j = 0,n2 - 1
        c = cos(angle)
        s = sin(angle)
        do i = j,maxifg - 1,n1
            l = i + n2
            xdum = x(i+1) - x(l+1)
            x(i+1) = x(i+1) + x(l+1)
            ydum = y(i+1) - y(l+1)
            y(i+1) = y(i+1) + y(l+1)
            x(l+1) = xdum * c - ydum * s
            y(l+1) = ydum * c + xdum * s
        end do ! i loop
        angle = real(j + 1,8) * argument
    end do !j loop
end do !k loop

j = 0
do i = 0,maxifg - 2
    if (i .lt. j) then
        xdum = x(j+1)
        x(j+1) = x(i+1)
        x(i+1) = xdum
        ydum = y(j+1)
        y(j+1) = y(i+1)
        y(i+1) = ydum
    end if
    k = maxifg / 2
    do while (k .lt. j + 1)
        j = j - k
        k = k / 2
    end do
    j = j + k
end do ! i loop

do i = 1,maxspc
    spec(i) = cmplx(x(i),y(i))
end do

deallocate (x,y)

end subroutine FFT



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
!  mysinc
!====================================================================
real function mysinc(x)

implicit none

real,parameter :: spi = 3.141592654
real,parameter :: spihalb = 1.570796327

real,intent(in) :: x
real :: xabs,xabsmod,xabsqu,xabsmodqu


xabs = abs(x) + 1.0e-8
xabsqu = xabs * xabs
!xabsmod = mod(xabs,spi)

mysinc = sin(xabs) / (xabs + 5.0e-8 * xabsqu * xabsqu)

!if (xabsmod .ge. spihalb) xabsmod = spi - xabsmod
!
!xabsmodqu = xabsmod * xabsmod
!xabsqu = xabs * xabs
!mysinc = (xabsmod &
!  * (1.0 + xabsmodqu * (-0.1666595 + xabsmodqu &
!  * (0.008315 - xabsmodqu * 0.0001855)))) / (xabs + 2.0e-7 * xabsqu * xabsqu)

end function mysinc



!====================================================================
!  next_free_unit
!====================================================================
integer function next_free_unit ()

implicit none

integer :: iu_free, istatus
logical :: is_open

iu_free = 9
is_open = .true.

do while (is_open .and. iu_free < 100)
    iu_free = iu_free+1
    inquire (unit=iu_free, opened=is_open, iostat=istatus)
    if (istatus .ne. 0) call warnout ('Error in inquiry!',0)
enddo

if (iu_free >= 100) call warnout ('No free unit < 100 found!',0)

next_free_unit = iu_free

end function next_free_unit



!====================================================================
!  OPUS_eval_char
!====================================================================
subroutine OPUS_eval_char(blocklength,binchar,charfilter,charwert)

use glob_prepro4,only : maxOPUSchar

implicit none

integer,intent(in) :: blocklength
character(len=blocklength),intent(in) :: binchar
character(len=3),intent(in) :: charfilter
character(len=maxOPUSchar),intent(out) :: charwert

integer(2) :: ityp,ireserved
integer :: ipos

ipos = index(binchar,charfilter//achar(0))
if (ipos .eq. 0) then
    call warnout('charfilter not found!',0)
end if

read(binchar(ipos+4:ipos+5),FMT='(A2)') ityp

read(binchar(ipos+6:ipos+7),FMT='(A2)') ireserved
    
if (ityp .ne. 2 .and. ityp .ne. 3) then
    call warnout('Inconsistent parameter kind in OPUS file!',0)
end if

charwert = '                                                  '
read(binchar(ipos+8:ipos+8+2*ireserved-1),FMT='(A)') charwert(1:2*ireserved)

end subroutine OPUS_eval_char



!====================================================================
!  OPUS_eval_int
!====================================================================
subroutine OPUS_eval_int(blocklength,binchar,charfilter,iwert)

implicit none

integer,intent(in) :: blocklength
character(len=blocklength),intent(in) :: binchar
character(len=3),intent(in) :: charfilter
integer,intent(out) :: iwert

integer(2) :: ityp,ireserved
integer :: ipos

ipos = index(binchar,charfilter//achar(0))
if (ipos .eq. 0) then
    call warnout('charfilter not found!',0)
end if

read(binchar(ipos+4:ipos+5),FMT='(A2)') ityp

read(binchar(ipos+6:ipos+7),FMT='(A2)') ireserved
    
if (ityp .ne. 0 .or. ireserved .ne. 2) then
    call warnout('Inconsistent parameter kind in OPUS file!',0)
end if

read(binchar(ipos+8:ipos+8+2*ireserved-1),FMT='(A4)') iwert

end subroutine OPUS_eval_int


!====================================================================
!  OPUS_eval_dble
!====================================================================
subroutine OPUS_eval_dble(blocklength,binchar,charfilter,dblewert)

implicit none

integer,intent(in) :: blocklength
character(len=blocklength),intent(in) :: binchar
character(len=3),intent(in) :: charfilter
real(8),intent(out) :: dblewert

integer(2) :: ityp,ireserved
integer :: ipos

ipos = index(binchar,charfilter//achar(0))
if (ipos .eq. 0) then
    call warnout('charfilter not found!',0)
end if

read(binchar(ipos+4:ipos+5),FMT='(A2)') ityp

read(binchar(ipos+6:ipos+7),FMT='(A2)') ireserved
    
if (ityp .ne. 1 .or. ireserved .ne. 4) then
    call warnout('Inconsistent parameter kind in OPUS file!',0)
end if

read(binchar(ipos+8:ipos+8+2*ireserved-1),FMT='(A8)') dblewert

end subroutine OPUS_eval_dble



!====================================================================
!  phasecorr
!====================================================================
subroutine phasecorr(ichan,errflag,cspec,spec)

use glob_prepro4,only : maxspc,phasa1max,phasa2max,phasa3max

implicit none

integer,intent(in) :: ichan
integer,intent(inout) :: errflag
complex,dimension(maxspc),intent(in) :: cspec
real,dimension(maxspc),intent(out) :: spec

integer :: i,j
complex(8) :: wrkcmplx
integer,dimension(2,4) :: irgn
real(8) :: a0re,a1re,a2re,a3re,a0im,a1im,a2im,a3im,phasre,phasim,phasnorm
real(8),dimension(4) :: midrgn
complex(8),dimension(4) :: refphas

if (ichan .eq. 1) then
    irgn(1,1) = 24250
    irgn(2,1) = 24750
    irgn(1,2) = 33250
    irgn(2,2) = 33750
    irgn(1,3) = 41250
    irgn(2,3) = 41750
    irgn(1,4) = 49250
    irgn(2,4) = 49750
else
    irgn(1,1) = 17000
    irgn(2,1) = 17200
    irgn(1,2) = 18500
    irgn(2,2) = 18700
    irgn(1,3) = 19500
    irgn(2,3) = 19700
    irgn(1,4) = 20800
    irgn(2,4) = 20900
end if

do i = 1,4
    midrgn(i) = 0.5d0 * real(irgn(1,i) + irgn(2,i),8)
end do

do i = 1,4
    wrkcmplx = (0.0d0,0.0d0)
    do j = irgn(1,i),irgn(2,i)
        wrkcmplx = wrkcmplx + cspec(j)
    end do
    refphas(i) = wrkcmplx / abs(wrkcmplx)
end do

a0re = real(refphas(1),8)
a1re = (real(refphas(2),8) - a0re) / (midrgn(2) - midrgn(1))
a2re = (real(refphas(3),8) - a0re - a1re * (midrgn(3) - midrgn(1))) &
  / ((midrgn(3) - midrgn(1)) * (midrgn(3) - midrgn(2)))
a3re = (real(refphas(4),8) - a0re - a1re * (midrgn(4) - midrgn(1)) &
  - a2re * (midrgn(4) - midrgn(1)) * (midrgn(4) - midrgn(2))) &
  / ((midrgn(4) - midrgn(1)) * (midrgn(4) - midrgn(2)) * (midrgn(4) - midrgn(3)))

a0im = aimag(refphas(1))
a1im = (aimag(refphas(2)) - a0im) / (midrgn(2) - midrgn(1))
a2im = (aimag(refphas(3)) - a0im - a1im * (midrgn(3) - midrgn(1))) &
  / ((midrgn(3) - midrgn(1)) * (midrgn(3) - midrgn(2)))
a3im = (aimag(refphas(4)) - a0im - a1im * (midrgn(4) - midrgn(1)) &
  - a2im * (midrgn(4) - midrgn(1)) * (midrgn(4) - midrgn(2))) &
  / ((midrgn(4) - midrgn(1)) * (midrgn(4) - midrgn(2)) * (midrgn(4) - midrgn(3)))

!print *, "ichan phase corr coeffs:",ichan
!print *,a0re,a1re,a2re,a3re
!print *,a0im,a1im,a2im,a3im

if (max(abs(a1re),abs(a1im)) .gt. phasa1max &
  .or. max(abs(a2re),abs(a2im)) .gt. phasa2max &
  .or. max(abs(a3re),abs(a3im)) .gt. phasa3max) then

    errflag = errflag + 1000000

end if

do i = 1,maxspc
    phasre = a0re + a1re * (real(i,8) - midrgn(1)) + a2re * (real(i,8) - midrgn(1)) &
      * (real(i,8) - midrgn(2)) + a3re * (real(i,8) - midrgn(1)) &
      * (real(i,8) - midrgn(2)) * (real(i,8) - midrgn(3))
    phasim = a0im + a1im * (real(i,8) - midrgn(1)) + a2im * (real(i,8) - midrgn(1)) &
      * (real(i,8) - midrgn(2)) + a3im * (real(i,8) - midrgn(1)) &
      * (real(i,8) - midrgn(2)) * (real(i,8) - midrgn(3))

    phasnorm = sqrt(phasre * phasre + phasim * phasim)

        spec(i) = (phasre * real(cspec(i),8) + phasim * aimag(cspec(i))) / phasnorm
        !spec(i) = (phasre * aimag(cspec(i)) - phasim * real(cspec(i),8)) / phasnorm
end do

end subroutine phasecorr



!====================================================================
!  prepare_sinc
!====================================================================
subroutine prepare_sinc(sinc)

use glob_prepro4, only : nconv,nzf,nsinc,pi

implicit none

real,dimension(-nsinc:nsinc),intent(out) :: sinc

integer :: i
real(8) :: x,xapo,apowert

sinc(0) = 1.0
do i = 1,nsinc
    xapo = real(i,8) / real(nzf * (nconv - 2),8)
    if (xapo .gt. 1.0) then
        xapo = pi
    else
        xapo = pi * xapo
    end if
    apowert = 0.5d0 * (1.0d0 + cos(xapo))
    x = pi * real(i,8) / real(nzf,8)
    sinc(i) = apowert * sin(x) / x
    sinc(-i) = sinc(i)
end do

end subroutine prepare_sinc



!====================================================================
!  read_ifg
!====================================================================
subroutine read_ifg(nofblock,nifg,dualifg,measfile,blocktype,blockptr &
  ,ifgfwd,ifgbwd,ifgfwd2,ifgbwd2)

use glob_prepro4, only : maxblock,maxifg,TCCONkind

implicit none

integer,intent(in) :: nofblock,nifg
logical,intent(in) :: dualifg
character(len=*),intent(in) :: measfile
integer,dimension(maxblock),intent(in) :: blocktype,blockptr
real,dimension(maxifg),intent(out) :: ifgfwd,ifgbwd,ifgfwd2,ifgbwd2

integer :: i,iunit,iowert,ptrifg,ptrifg2,next_free_unit

ifgfwd = 0.0
ifgbwd = 0.0
if (dualifg) then
    ifgfwd2 = 0.0
    ifgbwd2 = 0.0
end if

do i = 1,nofblock
   if (blocktype(i) .eq. 2055) then
        ptrifg = blockptr(i)
    end if
    if (blocktype(i) .eq. 34823) then
        ptrifg2 = blockptr(i)
    end if
end do

iunit = next_free_unit()

open (iunit,file = trim(measfile),form='unformatted',access ='stream',status = 'old',action = 'read',iostat = iowert)

if (iowert .ne. 0) then
    print *,trim(measfile)
    call warnout('Cannot open measurement file!',0)
end if

! In case of Ka 125HR OPUS files swap first and second channel
if (TCCONkind .eq. 2) then
    read(unit = iunit,pos = ptrifg + 1) ifgfwd2(1:nifg)
    do i = nifg,1,-1
        read(unit = iunit) ifgbwd2(i)
    end do
else
    read(unit = iunit,pos = ptrifg + 1) ifgfwd(1:nifg)
    do i = nifg,1,-1
        read(unit = iunit) ifgbwd(i)
    end do
end if

if (dualifg) then
    ! In case of Ka 125HR OPUS files swap first and second channel
    if (TCCONkind .eq. 2) then
        read(unit = iunit,pos = ptrifg2 + 1) ifgfwd(1:nifg)
        do i = nifg,1,-1
            read(unit = iunit) ifgbwd(i)
        end do
    else
        read(unit = iunit,pos = ptrifg2 + 1) ifgfwd2(1:nifg)
        do i = nifg,1,-1
            read(unit = iunit) ifgbwd2(i)
        end do
    end if
end if

close (iunit)

end subroutine read_ifg



!====================================================================
!  read_input: Einlesen der Eingabedatei
!====================================================================
subroutine read_input(inpdatei)

use glob_prepro4

implicit none

character(len=*),intent(in) :: inpdatei

character(len=300) :: zeile
logical :: marke,decfileda,decsize
integer :: iunit,iowert,imeas,next_free_unit,nfilebytes

iunit = next_free_unit()
open (iunit,file = trim(inpdatei),status = 'old',iostat = iowert)
if (iowert .ne. 0) then
    print *,trim(inpdatei)
    call warnout('Cannot open input file!',0)
end if

call gonext(iunit,.false.)
read(iunit,*) checkoutdec
read(iunit,*) mpowFFT
read(iunit,*) DCmin
read(iunit,*) DCvar

call gonext(iunit,.false.)
read(iunit,*) ILSapo,ILSphas
read(iunit,*) ILSapo2,ILSphas2

call gonext(iunit,.false.)
read(iunit,*) obsfixdec
read(iunit,*) obslocation
read(iunit,*) toffseth_UT
if (obsfixdec) then
    read(iunit,*) obsfixlatdeg,obsfixlondeg,obsfixaltkm
else
    continue
end if

call gonext(iunit,.false.)
read(iunit,'(L)') quietrundec
read(iunit,'(A)') diagoutpath
read(iunit,'(A)') binoutpath
if (diagoutpath .eq. 'standard') diagoutpath = 'diagnosis'

call gonext(iunit,.false.)
read(iunit,'(A)') infotext

call gonext(iunit,.false.)
! determine number of raw measurements to treat
marke = .false.
imeas = 0
do while (.not. marke)
    read(iunit,'(A)') zeile
    if (zeile(1:3) .eq. '***') then
        marke = .true.
    else        
        ! test file existence and size here
        inquire(file = zeile,exist = decfileda,size = nfilebytes)
        if (.not. decfileda) then
            print *,zeile
            call warnout('spectrum file does not exist!',0)
        end if
        if (nfilebytes .lt. minfilesize) then
            decsize = .false.
        else
            decsize = .true.
        end if
        if (decsize) imeas = imeas + 1
    end if
end do

close (iunit)
nmeas = imeas

end subroutine read_input



!====================================================================
!  read names of all files to be processed
!====================================================================
subroutine read_meas_files(inpdatei,nmeas,measfile)

use glob_prepro4, only : lengthcharmeas,minfilesize

implicit none

character(len=*),intent(in) :: inpdatei
integer,intent(in) :: nmeas
character(len=lengthcharmeas),dimension(nmeas),intent(out) :: measfile

logical :: marke,decfileda,decsize
character(len=lengthcharmeas) :: zeile
integer :: i,imeas,imeasall,iunit,iowert,next_free_unit,nfilebytes

iunit = next_free_unit()

open (iunit,file = trim(inpdatei),status = 'old',iostat = iowert)
if (iowert .ne. 0) then
    print *,trim(inpdatei)
    call warnout('Cannot open input file!',0)
end if

do i = 1,6
    call gonext(iunit,.false.)
end do

marke = .false.
imeas = 0
do while (.not. marke)
    read(iunit,'(A)') zeile
    if (zeile(1:3) .eq. '***') then
        marke = .true.
    else        
        ! test file size here
        inquire(file = zeile,exist = decfileda,size = nfilebytes)
        if (.not. decfileda) then
            print *,zeile
            call warnout('spectrum file does not exist!',0)
        end if
        if (nfilebytes .lt. minfilesize) then
            decsize = .false.
        else
            decsize = .true.
        end if
        if (decsize) then
            imeas = imeas + 1
            measfile(imeas) = trim(zeile)
            print *,trim(measfile(imeas))
        end if
    end if
end do

close (iunit)

end subroutine read_meas_files



!====================================================================
!  read_opus_dir
!====================================================================
subroutine read_opus_dir(measfile,nptrfirstdir,nofblock,blocktype &
  ,blocklength,blockptr,dualifg,nifg)

use glob_prepro4,only : maxblock,maxblength,maxifg

implicit none

character(len=*),intent(in) :: measfile
integer,intent(in) :: nptrfirstdir,nofblock
integer,dimension(maxblock),intent(out) :: blocktype,blocklength,blockptr
logical,intent(out) :: dualifg
integer,intent(out) :: nifg

character(len=1) :: charbyte
integer :: i,nifga,nifgb,iwert,magic,iunit,iowert,next_free_unit
real(8) :: progver

iunit = next_free_unit()

open (iunit,file = trim(measfile),form='unformatted',access ='stream',status = 'old',action = 'read',iostat = iowert)

do i = 1,nptrfirstdir
    read(iunit) charbyte
end do

do i = 1,nofblock
    read(iunit) iwert
    blocktype(i) = mod(iwert,2**16)
    read(iunit) blocklength(i)
    blocklength(i) = 4 * blocklength(i)
    read(iunit) blockptr(i)
end do

close (iunit)

nifga = 0
nifgb = 0
dualifg = .false.
do i = 1,nofblock
   if (blocktype(i) .eq. 2055) then
        nifga = blocklength(i)
    end if
    ! dual channel?
    if (blocktype(i) .eq. 34823) then
        dualifg = .true.
        nifgb = blocklength(i)
    end if
end do

if (nifga .eq. 0) then
    print *,measfile
    call warnout('Zero IFG block size!',0)
end if

if (dualifg .and. nifga .ne. nifgb) then
    print *,measfile
    call warnout('Differing sizes of dual channel IFGs!',0)
else
    if (mod(nifga,8) .ne. 0) then
        print*, measfile
        call warnout('Unexpected IFG size!',0)
    end if
    nifg = nifga / 8
end if

if (mod(nifg,2) .ne. 0) then
    print *,measfile
    call warnout('nifg not even!',0)
end if

if (nifg .gt. maxifg) then
    print *,measfile
    call warnout('IFG size too big!',0)
end if

end subroutine read_opus_dir



!====================================================================
!  read_opus_hdr
!====================================================================
subroutine read_opus_hdr(measfile,nptrfirstdir,nofblock)

use glob_prepro4, only : maxblock

implicit none

character(len=*),intent(in) :: measfile
integer,intent(out) :: nptrfirstdir,nofblock

character(len=1) :: charbyte
integer :: i,ntest,magic,iunit,iowert,next_free_unit
real(8) :: progver

iunit = next_free_unit()

open (iunit,file = trim(measfile),form='unformatted',access ='stream',status = 'old',action = 'read',iostat = iowert)
if (iowert .ne. 0) then
    print *,trim(measfile)
    call warnout('Cannot open measurement file!',0)
end if

read(iunit) magic
if (magic .ne. -16905718) then
    print *,'measurement file:',trim(measfile)
    call warnout('Not an OPUS file!',0)
end if

read(iunit) progver
!print *,progver

read(iunit) nptrfirstdir
!print *,nptrfirstdir

read(iunit) ntest ! Angabe maxblock
!print *,ntest

read(iunit) nofblock
!print *,nofblock
if (nofblock .gt. maxblock) then
    print *,'measurement file:',trim(measfile)
    call warnout('nofblock too big!',0)
end if

close (iunit)

end subroutine read_opus_hdr



!====================================================================
!  read OPUS parameters
!              
!====================================================================
subroutine read_opus_parms(imeas,measfile,nofblock,blocktype,blocklength,blockptr)

use glob_prepro4,only : maxblock,maxblength
use glob_OPUSparms

implicit none

character(len=*),intent(in) :: measfile
integer,intent(in) :: imeas,nofblock
integer,dimension(maxblock),intent(in) :: blocktype,blocklength,blockptr

integer :: i,iunit,iowert,next_free_unit
character(len=maxblength) :: binchar

! read variables from blocktype 32: HFL,LWN,GFW,GBW,TSC,SSM
do i = 1,nofblock
   if (blocktype(i) .eq. 32) exit
end do

iunit = next_free_unit()

open (iunit,file = trim(measfile),form='unformatted',access ='stream',status = 'old',action = 'read',iostat = iowert)
if (iowert .ne. 0) then
    print *,trim(measfile)
    call warnout('Cannot open measurement file!',0)
end if

if (blocklength(i) .gt. maxblength) then
    print *,trim(measfile)
    call warnout('Max blocklength exceeded!',0)
end if

read(unit = iunit,pos = blockptr(i) + 1) binchar(1:blocklength(i))
close (iunit)

call OPUS_eval_int(blocklength(i),binchar,'GFW',OPUS_parms(imeas)%GFW)
call OPUS_eval_int(blocklength(i),binchar,'GBW',OPUS_parms(imeas)%GBW)
call OPUS_eval_dble(blocklength(i),binchar,'HFL',OPUS_parms(imeas)%HFL)
call OPUS_eval_dble(blocklength(i),binchar,'LWN',OPUS_parms(imeas)%LWN)
call OPUS_eval_dble(blocklength(i),binchar,'TSC',OPUS_parms(imeas)%TSC)

! read variables from blocktype 48: NSS,AQM
do i = 1,nofblock
   if (blocktype(i) .eq. 48) exit
end do

iunit = next_free_unit()

open (iunit,file = trim(measfile),form='unformatted',access ='stream',status = 'old',action = 'read',iostat = iowert)
if (iowert .ne. 0) then
    print *,trim(measfile)
    call warnout('Cannot open measurement file!',0)
end if

if (blocklength(i) .gt. maxblength) then
    print *,trim(measfile)
    call warnout('Max blocklength exceeded!',0)
end if

read(unit = iunit,pos = blockptr(i) + 1) binchar(1:blocklength(i))
close (iunit)

!call OPUS_eval_char(blocklength,binchar,'VEL',OPUS_parms(imeas)%VEL)
!print*,OPUS_parms(imeas)%VEL

call OPUS_eval_int(blocklength(i),binchar,'NSS',OPUS_parms(imeas)%NSS)
call OPUS_eval_char(blocklength(i),binchar,'AQM',OPUS_parms(imeas)%AQM)
call OPUS_eval_dble(blocklength(i),binchar,'RES',OPUS_parms(imeas)%RES)

! read variables from blocktype 96: VEL,HPF,LPF
do i = 1,nofblock
   if (blocktype(i) .eq. 96) exit
end do

iunit = next_free_unit()

open (iunit,file = trim(measfile),form='unformatted',access ='stream',status = 'old',action = 'read',iostat = iowert)
if (iowert .ne. 0) then
    print *,trim(measfile)
    call warnout('Cannot open measurement file!',0)
end if

if (blocklength(i) .gt. maxblength) then
    print *,trim(measfile)
    call warnout('Max blocklength exceeded!',0)
end if

read(unit = iunit,pos = blockptr(i) + 1) binchar(1:blocklength(i))
close (iunit)

call OPUS_eval_char(blocklength(i),binchar,'VEL',OPUS_parms(imeas)%VEL)
call OPUS_eval_char(blocklength(i),binchar,'HPF',OPUS_parms(imeas)%HPF)
call OPUS_eval_char(blocklength(i),binchar,'LPF',OPUS_parms(imeas)%LPF)

! read variables from blocktype 2071: DAT,TIM

do i = 1,nofblock
   if (blocktype(i) .eq. 2071) exit
end do

iunit = next_free_unit()

open (iunit,file = trim(measfile),form='unformatted',access ='stream',status = 'old',action = 'read',iostat = iowert)
if (iowert .ne. 0) then
    print *,trim(measfile)
    call warnout('Cannot open measurement file!',0)
end if

if (blocklength(i) .gt. maxblength) then
    print *,trim(measfile)
    call warnout('Max blocklength exceeded!',0)
end if

read(unit = iunit,pos = blockptr(i) + 1) binchar(1:blocklength(i))
close (iunit)

call OPUS_eval_char(blocklength(i),binchar,'DAT',OPUS_parms(imeas)%DAT)
call OPUS_eval_char(blocklength(i),binchar,'TIM',OPUS_parms(imeas)%TIM)

end subroutine read_opus_parms



!====================================================================
!  read_refspec
!====================================================================
subroutine read_refspec(refspecfile,maxspc,refspec)

implicit none

character(len=*),intent(in) :: refspecfile
integer,intent(in) :: maxspc
real,dimension(maxspc),intent(out) :: refspec

integer :: i,icount,iunit,iowert,next_free_unit
real :: wert

iunit = next_free_unit()
! check availability of file, number of file entries
open (iunit,file = trim(refspecfile),status = 'old',iostat = iowert)
if (iowert .ne. 0) then
    print *,trim(refspecfile)
    call warnout('Cannot open refspec file!',0)
end if

icount = 0
do
    read(iunit,*,end = 102) wert
    icount = icount + 1
end do
102 continue
close (iunit)

if (icount .ne. maxspc) then
    print *,'maxspc:',maxspc
    print *,'icount:',icount
    call warnout('Incompatible # of entries in refspec!',0)
end if

iunit = next_free_unit()
open (iunit,file = trim(refspecfile),status = 'old',iostat = iowert)
do i = 1,icount
    read(iunit,*) refspec(i)
end do
close (iunit)

end subroutine read_refspec



!====================================================================
!  resample
!====================================================================
subroutine resample(ichan,sinc,spec,specrs)

use glob_prepro4, only : maxspc,maxspcrs,nsinc,nzf,nconv &
  ,nuelas,nuersstart,nuersstop,nuersstart2,nuersstop2

implicit none

integer,intent(in) :: ichan
real,dimension(-nsinc:nsinc),intent(in) :: sinc
real,dimension(maxspc),intent(in) :: spec
real,dimension(maxspcrs),intent(out) :: specrs

integer :: i,j,k,jmid,imsstart,imsstop,ifft,isinc
real(8) :: dnuefft,dnuers,nuestart,nuestop,sumwert,xfft,xsinc,restfft,restsinc,a0,a1,a2
real(8),dimension(3) :: y

dnuefft = nuelas / real(maxspc - 1,8)
dnuers = nuelas / real(maxspcrs - 1,8)

if (ichan .eq. 1) then
    nuestart = nuersstart
    nuestop = nuersstop
else
    nuestart = nuersstart2
    nuestop = nuersstop2
end if

imsstart = 1 + nuestart / dnuers
imsstop = 1 + nuestop / dnuers

specrs(1:imsstart-1) = 0.0
specrs(imsstop+1:maxspcrs) = 0.0

do i = imsstart,imsstop ! loop on minimally sampled grid

    xfft = 1.0d0 + real(i - 1,8) * dnuers / dnuefft
    ifft = nint(xfft)
    restfft = xfft - real(ifft,8) ! in interval -0.5 ... 0.5

    xsinc = restfft * real(nzf,8) ! in interval -0.5 * nzf ... 0.5 * nzf
    isinc = nint(xsinc)
    restsinc = xsinc - real(isinc,8) ! in interval -0.5 ... 0.5

    ! convolution with sinc on FFT grid
    do j = -1,1
        sumwert = 0.0d0
        do k = -nconv + 1,nconv - 1
            sumwert = sumwert + spec(ifft+k) * sinc(k*nzf-isinc-j)
        end do
        y(2+j) = sumwert
    end do

    ! quadratic interpolation to desired position on resampling grid
    a0 = y(2)
    a1 = 0.5d0 * (y(3) - y(1))
    a2 = 0.5d0 * (y(3) + y(1)) - y(2)
    
    specrs(i) = a0 + restsinc * (a1 + restsinc * a2)

end do

end subroutine resample



!====================================================================
!  resample
!====================================================================
subroutine resample_bf(ichan,sinc,spec,specrs)

use glob_prepro4, only : maxspc,maxspcrs,nsinc,nconv,nuelas,pi,OPDmax &
  ,nuersstart,nuersstop,nuersstart2,nuersstop2

implicit none

integer,intent(in) :: ichan
real,dimension(-nsinc:nsinc),intent(in) :: sinc
real,dimension(maxspc),intent(in) :: spec
real,dimension(maxspcrs),intent(out) :: specrs

integer :: i,j,ifft,imsstart,imsstop
real(8) :: nuestart,nuestop,dnuefft,dnuers,sumwert,dx,dxapo,sincwert &
  ,norm,apowert,faktor,nuers
real(8),dimension(-nconv:nconv) :: apo

dnuefft = nuelas / real(maxspc - 1,8)
dnuers = nuelas / real(maxspcrs - 1,8)

if (ichan .eq. 1) then
    imsstart = 1 + nuersstart / dnuers
    imsstop = 1 + nuersstop / dnuers    
else
    imsstart = 1 + nuersstart2 / dnuers
    imsstop = 1 + nuersstop2 / dnuers
end if

specrs(1:imsstart-1) = 0.0
specrs(imsstop+1:maxspcrs) = 0.0

do i = -nconv,nconv
    dxapo = pi * real(i,8) / real(nconv,8)
    apo(i) = 0.5d0 * (1.0d0 + cos(dxapo))
end do

norm = dnuefft / dnuers
faktor = 2.0d0 * OPDmax * pi

do i = imsstart,imsstop ! loop on minimally sampled grid

    ifft = nint(1.0d0 + real(i - 1,8) * dnuers / dnuefft)
    nuers = dnuers * real(i - 1,8)

    sumwert = 0.0d0
    do j = ifft - nconv,ifft + nconv
        dx = faktor * (1.0d-6 + abs(nuers - dnuefft * real(j - 1,8)))        
        sincwert = apo(j-ifft) * sin(dx) / dx
        sumwert = sumwert + sincwert * spec(j)
    end do
    specrs(i) = norm * sumwert

end do

end subroutine resample_bf



!====================================================================
!  smoothspec (impose some self apo on TCCON spectra)
!====================================================================
subroutine smoothspec(nspc,spec)

implicit none

integer,intent(in) :: nspc
real,dimension(nspc),intent(inout) :: spec

integer,parameter :: niter = 3
real,parameter :: ampnull = 4.4d-4

integer :: iiter,ispc
real(8) :: werta,wertb,wertc,faktor,amp

faktor = 1.0d0 / real(nspc,8)

do iiter = 1,niter
    werta = real(spec(1),8)
    wertb = real(spec(2),8)
    do ispc = 2,nspc - 1
        amp = ampnull * real(ispc,8) * faktor
        wertc = real(spec(ispc+1),8)
        spec(ispc) = amp * werta + (1.0d0 - 2.0d0 * amp) * wertb + amp * wertc
        werta = wertb
        wertb = wertc
    end do
end do

end subroutine smoothspec



!====================================================================
!  tofile_binspec
!====================================================================
subroutine tofile_binspec(ichan,measfile,YYMMDDlocal,HHMMSSlocal,YYMMDDUT &
  ,UTh,durationsec,astrelev,azimuth,spec)

use glob_prepro4

implicit none

integer,intent(in) :: ichan
character(len=*),intent(in) :: measfile
character(len=6),intent(in) :: YYMMDDlocal,HHMMSSlocal,YYMMDDUT
real,intent(in) :: UTh,durationsec,astrelev,azimuth
real,dimension(maxspcrs),intent(in) :: spec

character(len=200) :: ausdatei
character(len=20) :: numchar
character(len=2) :: eol
integer :: imsstart,imsstop,nofpts_out,iscan,istop,ifilter,iunit,next_free_unit
real(8) :: dnuers,firstnue_out,lastnue_out

dnuers = nuelas / real(maxspcrs - 1,8)
iscan = scan(measfile,pathstr,.true.)
istop = len_trim(measfile)

if (ichan .eq. 1) then
    imsstart = 1 + nuersstart / dnuers
    imsstop = 1 + nuersstop / dnuers
    ifilter = 10
    if (binoutpath(1:8) .eq. 'standard') then
        ausdatei = measfile(1:iscan-1)//pathstr//'cal'//pathstr//YYMMDDlocal//'_'//HHMMSSlocal//'SN.BIN'
    else
        ausdatei = trim(binoutpath)//pathstr//YYMMDDlocal//'_'//HHMMSSlocal//'SN.BIN'
    end if
else
    imsstart = 1 + nuersstart2 / dnuers
    imsstop = 1 + nuersstop2 / dnuers
    ifilter = 12
    if (binoutpath(1:8) .eq. 'standard') then
        ausdatei = measfile(1:iscan-1)//pathstr//'cal'//pathstr//YYMMDDlocal//'_'//HHMMSSlocal//'SM.BIN'
    else
        ausdatei = trim(binoutpath)//pathstr//YYMMDDlocal//'_'//HHMMSSlocal//'SM.BIN'
    end if
end if
nofpts_out = imsstop - imsstart + 1
firstnue_out = real(imsstart - 1,8) * dnuers
lastnue_out = real(imsstop - 1,8) * dnuers

! end of line 0D+0A ASCI: 13 + 10
eol = char(13)//char(10)

iunit = next_free_unit()
open (iunit,file = trim(ausdatei),form='unformatted',access ='stream',status = 'unknown',action = 'write')

! Erster Block: Beobachtungsort,Datum und Zeit
write (iunit) 'Location',eol
write (iunit) 'Date',eol
write (iunit) 'Time eff. UT [h,decimals]',eol
write (iunit) 'Unrefracted elevation [deg]',eol
write (iunit) 'Azimuth [deg]',eol
write (iunit) 'Duration of measurement [s]',eol
write (iunit) 'Latitude [deg] (negative South)',eol
write (iunit) 'Longitude [deg] (negative west)',eol
write (iunit) 'observer altitude [km]',eol
write (iunit) 'OPUS spectrum name',eol
write (iunit) '$',eol
write (iunit) obslocation,eol
write (iunit) YYMMDDUT,eol
numchar = '              '
write (numchar,'(F9.5)') UTh
write (iunit) trim(numchar),eol
numchar = '              '
write (numchar,'(F9.5)') astrelev
write (iunit) trim(numchar),eol
numchar = '              '
write (numchar,'(F9.4)') azimuth
write (iunit) trim(numchar),eol
numchar = '              '
write (numchar,'(F9.1)') durationsec
write (iunit) trim(numchar),eol
numchar = '              '
write (numchar,'(F10.5)') obsfixlatdeg
write (iunit) trim(numchar),eol
numchar = '              '
write (numchar,'(F10.5)') obsfixlondeg
write (iunit) trim(numchar),eol
numchar = '              '
write (numchar,'(F9.5)') obsfixaltkm
write (iunit) trim(numchar),eol
write (iunit) measfile(iscan+1:istop),eol,eol

! Zweiter Block: Filter,OPDmax,APTdiam,Fcoll
write (iunit) 'Filter',eol
write (iunit) 'OPDmax [cm]',eol
write (iunit) 'semi FOV [rad]',eol
write (iunit) '$',eol
numchar = '              '
write (numchar,'(I2)') ifilter
write (iunit) trim(numchar),eol
numchar = '              '
write (numchar,'(F8.4)') OPDmax
write (iunit) trim(numchar),eol
numchar = '              '
write (numchar,'(ES8.2)') semiFOV
write (iunit) trim(numchar),eol,eol

! Dritter Block: Modulationseffizienz
write (iunit) 'ILS simple(1) or extended(2)',eol
write (iunit) 'modulation efficiency',eol
write (iunit) '$',eol
numchar = '              '
write (numchar,'(I2)') 1
write (iunit) trim(numchar),eol
if (ichan .eq. 1) then
    numchar = '              '
    write (numchar,'(ES10.3)') ilsapo
    write (iunit) trim(numchar)
    write (iunit) ','
    numchar = '              '
    write (numchar,'(ES10.3)') ilsphas
    write (iunit) trim(numchar),eol
else
    numchar = '              '
    write (numchar,'(ES10.3)') ilsapo2
    write (iunit) trim(numchar)
    write (iunit) ','
    numchar = '              '
    write (numchar,'(ES10.3)') ilsphas2
    write (iunit) trim(numchar),eol
end if
write (iunit) eol

! Vierter Block: firstnue,lastnue,deltanue,nofpts
write (iunit) 'firstnue',eol
write (iunit) 'lastnue',eol
write (iunit) 'deltanue',eol
write (iunit) 'Ngridpts',eol
write (iunit) '$',eol
numchar = '              '
write (numchar,'(F13.7)') firstnue_out
write (iunit) trim(numchar),eol
numchar = '              '
write (numchar,'(F13.7)') lastnue_out
write (iunit) trim(numchar),eol
numchar = '              '
write (numchar,'(ES16.9)') dnuers
write (iunit) trim(numchar),eol
write (numchar,'(I7)') nofpts_out
write (iunit) trim(numchar),eol,eol

! Fuenfter Block: Comments
write (iunit) 'Comments',eol
write (iunit) '$',eol
write (iunit) trim(infotext),eol,eol

! Sechster Block: bin�res Spektrum: firstwvnr(real*8),dwvnr(real*8)
! ,nofpts,ordinatenwerte(real*4)
write (iunit) '$',eol
write (iunit) firstnue_out
write (iunit) dnuers
write (iunit) nofpts_out
write (iunit) spec(imsstart:imsstop)

close (iunit)

end subroutine tofile_binspec



!====================================================================
!  tofile_cspec
!====================================================================
subroutine tofile_cspec(ausdatei,nspec,cspec)

implicit none

character(len=*),intent(in) :: ausdatei
integer,intent(in) :: nspec
complex,dimension(nspec),intent(in) :: cspec

integer :: i,iunit,next_free_unit

iunit = next_free_unit()

open (iunit,file = ausdatei,status = 'replace')

do i = 1,nspec
    write(iunit,'(ES13.6,1X,ES13.6)') real(cspec(i)),aimag(cspec(i))
end do

close (iunit)

end subroutine tofile_cspec



!====================================================================
!  tofile_spec
!====================================================================
subroutine tofile_spec(ausdatei,nspec,spec)

implicit none

character(len=*),intent(in) :: ausdatei
integer,intent(in) :: nspec
real,dimension(nspec),intent(in) :: spec

integer :: i,iunit,next_free_unit

iunit = next_free_unit()

open (iunit,file = ausdatei,status = 'replace')

do i = 1,nspec
    write(iunit,'(ES13.6)') spec(i)
end do

close (iunit)

end subroutine tofile_spec



!====================================================================
!  tofile_ifg
!====================================================================
subroutine tofile_ifg(ausdatei,nifg,ifg)

implicit none

character(len=*),intent(in) :: ausdatei
integer,intent(in) :: nifg
real,dimension(nifg),intent(in) :: ifg

integer :: i,iunit,next_free_unit

iunit = next_free_unit()

open (iunit,file = ausdatei,status = 'replace')

do i = 1,nifg
    write(iunit,'(ES13.6)') ifg(i)
end do

close (iunit)

end subroutine tofile_ifg



!====================================================================
!� Warnung rausschreiben und Programm evtl. beenden
!====================================================================
subroutine warnout(text,predec)

use ISO_FORTRAN_ENV, only : ERROR_UNIT
use glob_prepro4, only : quietrundec

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
