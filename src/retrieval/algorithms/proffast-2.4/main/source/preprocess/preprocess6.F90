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

program preprocess6

use glob_prepro6

implicit none

logical :: dateidadec,reftrmdec
integer :: imeas,itest,iunit,iscan,narg,next_free_unit
character(len=200) :: inputdatei,logdatei,logdatei_test
character(len=7) :: idchar,imeaschar
character(len=4) :: argchar

character(len=lengthcharmeas),dimension(:),allocatable :: measfile
integer(8),dimension(:),allocatable :: errflag,errflag_CO 
integer,dimension(:),allocatable :: nptrfirstdir,nofblock,nifg &
  ,icbfwd,icbbwd,icbfwd2,icbbwd2
integer,dimension(:,:),allocatable :: blocktype,blocklength,blockptr

real(8),dimension(:),allocatable :: JDdate
real,dimension(:),allocatable :: UTh,durationsec,astrelev,azimuth

character(len=6),dimension(:),allocatable :: YYMMDDlocal,HHMMSSlocal,YYMMDDUT

real,dimension(:,:),allocatable :: reftrmT
real,dimension(:),allocatable :: refspec,refspec2,refphas,reftrm,sinc
real,dimension(:),allocatable :: cbfwd,cbbwd,cbfwd2,cbbwd2
real,dimension(:),allocatable :: obslatdeg,obslondeg,obsaltkm

real,dimension(:),allocatable :: dcmeanfwd,dcmeanbwd,dcmeanfwd2,dcmeanbwd2
real,dimension(:),allocatable :: dcminfwd,dcminbwd,dcminfwd2,dcminbwd2
real,dimension(:),allocatable :: dcmaxfwd,dcmaxbwd,dcmaxfwd2,dcmaxbwd2

! arrays for processing loop
real(8),dimension(:),allocatable :: anaphasfwd,anaphasbwd,anaphasfwd2,anaphasbwd2
complex,dimension(:),allocatable :: phasfwd,phasbwd,phasfwd2,phasbwd2
real,dimension(:),allocatable :: ifgfwd,ifgbwd,ifgfwd2,ifgbwd2,ifgfwdp,ifgbwdp,ifgfwdp2,ifgbwdp2
real,dimension(:),allocatable :: specfwd,specbwd,specfwd2,specbwd2
real,dimension(:),allocatable :: specfwdrs,specbwdrs,specfwd2rs,specbwd2rs
real,dimension(:),allocatable :: specmeanrs,specmean2rs
complex,dimension(:),allocatable :: cspecfwd,cspecbwd,cspecfwd2,cspecbwd2,cspecfwdp,cspecbwdp,cspecfwdp2,cspecbwdp2

!====================================================================
!  read command argument
!  read input file
!====================================================================
call get_command_argument(1,inputdatei)
print *,'Reading input file...'
call read_input(trim(inputdatei))
print *,'Done!'
print *,'Number of raw measurements to be processed:',nmeas

if (nmeas .gt. maxmeas) then
    print *,'nmeas maxmeas: ',nmeas,maxmeas
    call warnout ('Too many files for processing!',0)
end if

!====================================================================
!  set ifg, spectral points and OPDmax according to input choice of mpowFFT
!====================================================================
select case (mpowFFT)
    case (17)
        OPDmax = 1.8d0 ! equivalent to Bruker Res 0.5 cm-1
        ifgradius = 56873            
    case (19)
        OPDmax = 4.5d0
        ifgradius = 142182
    case (20)
        OPDmax = 16.2d0
        ifgradius = 511857
    case (181)
        mpowFFT = 18
        OPDmax = 2.5d0 ! equivalent to Bruker Res 0.36 cm-1
        ifgradius = 78990
    case (182)
        mpowFFT = 18
        OPDmax = 3.0d0 ! equivalent to Bruker Res 0.3 cm-1
        ifgradius = 94788
    case default
        call warnout("Invalid choice of mpowFFT (allowed: 17, 181/182, 19, 20)!",0)
end select
maxspcrs = ifgradius + 1
maxifg = 2**mpowFFT
maxspc = maxifg / 2 

!====================================================================
!  allocation of general arrays, init sinc, read reference spectrum (for nue cal check)
!====================================================================
allocate (errflag(nmeas),errflag_CO(nmeas))
allocate (measfile(nmeas),nptrfirstdir(nmeas),nofblock(nmeas),nifg(nmeas))
allocate (icbfwd(nmeas),icbbwd(nmeas),icbfwd2(nmeas),icbbwd2(nmeas))
allocate (cbfwd(nmeas),cbbwd(nmeas),cbfwd2(nmeas),cbbwd2(nmeas))

allocate (obslatdeg(maxmeas),obslondeg(maxmeas),obsaltkm(maxmeas))
allocate (blocktype(maxblock,nmeas),blocklength(maxblock,nmeas),blockptr(maxblock,nmeas))
allocate (YYMMDDlocal(nmeas),HHMMSSlocal(nmeas),YYMMDDUT(nmeas))
allocate (JDdate(nmeas),UTh(nmeas),durationsec(nmeas),astrelev(nmeas),azimuth(nmeas))
nsinc = nzf * nconv
allocate (sinc(-nsinc:nsinc))
allocate (refspec(maxspc),refspec2(maxspc),refphas(maxspc),reftrm(maxspc))

! added by Moritz Makowski to perform the DC min / DC var filtering in retrospective
allocate (dcmeanfwd(nmeas),dcmeanbwd(nmeas),dcmeanfwd2(nmeas),dcmeanbwd2(nmeas))
allocate (dcminfwd(nmeas),dcminbwd(nmeas),dcminfwd2(nmeas),dcminbwd2(nmeas))
allocate (dcmaxfwd(nmeas),dcmaxbwd(nmeas),dcmaxfwd2(nmeas),dcmaxbwd2(nmeas))

call prepare_sinc(sinc)

if (checkoutdec) then 
    call tofile_spec(trim(diagoutpath)//pathstr//'sinc.dat',2*nsinc+1,sinc(-nsinc:nsinc))
end if

call read_refspec('refspec.dat',maxspc,refspec)
call read_refspec('refspec2.dat',maxspc,refspec2)

inquire (file = 'refphase.inp',exist = dateidadec)
if (dateidadec) then
    print *,'Optional phase reference file detected...'
    call read_refspec('refphase.inp',maxspc,refphas)
else
    refphas = 0.0
end if

inquire (file = 'reftrm.inp',exist = dateidadec)
if (dateidadec) then
    print *,'Optional trm reference file detected...'
    allocate (reftrmT(maxT,maxspc))
    reftrmdec = .true.
    call read_reftrmT('reftrm.inp',maxT,maxspc,reftrmT)
else
    reftrmdec = .false.
end if

!====================================================================
!  read file names
!====================================================================
print *,'Reading file names'
call read_meas_files(trim(inputdatei),nmeas,measfile,obslatdeg,obslondeg,obsaltkm)
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
      ,blockptr(1:maxblock,imeas),nifg(imeas))
    call read_opus_parms(imeas,measfile(imeas),nofblock(imeas) &
      ,blocktype(1:maxblock,imeas),blocklength(1:maxblock,imeas),blockptr(1:maxblock,imeas))

    ! check formal consistency of file with COCCON / preprocessor demands
    call checkOPUSparms(measfile(imeas),imeas)

end do

do imeas = 1,nmeas
    ! calculate solar position
    call calcsolpos(imeas,nifg(imeas),obslatdeg(imeas),obslondeg(imeas),JDdate(imeas) &
      ,YYMMDDlocal(imeas),HHMMSSlocal(imeas),YYMMDDUT(imeas),UTh(imeas) &
      ,durationsec(imeas),astrelev(imeas),azimuth(imeas))
    ! set error flag if astronomical (solar elevation below 1 deg)
    if (astrelev(imeas) .lt. 1.0) then
        errflag(imeas) = errflag(imeas) + 1
        errflag_CO(imeas) = errflag_CO(imeas) + 1
    end if     
end do

! allocate interferogram and spectrum workspace for processing loop
allocate (anaphasfwd(nphas),anaphasbwd(nphas),anaphasfwd2(nphas),anaphasbwd2(nphas))
allocate (phasfwd(nphaspts),phasbwd(nphaspts),phasfwd2(nphaspts),phasbwd2(nphaspts))
allocate (ifgfwd(maxifg),ifgbwd(maxifg),ifgfwd2(maxifg),ifgbwd2(maxifg))
allocate (ifgfwdp(maxifg),ifgbwdp(maxifg),ifgfwdp2(maxifg),ifgbwdp2(maxifg))
allocate (cspecfwd(maxspc),cspecbwd(maxspc),cspecfwd2(maxspc),cspecbwd2(maxspc))
allocate (cspecfwdp(maxspc),cspecbwdp(maxspc),cspecfwdp2(maxspc),cspecbwdp2(maxspc))
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

    write (imeaschar,'(I7)') imeas
    idchar = adjustl(imeaschar)
    
    
    print *,'Reading file from disc ...',imeas

    ! read OPUS file
    call read_ifg(nofblock(imeas),nifg(imeas),measfile(imeas) &
      ,blocktype(1:maxblock,imeas),blockptr(1:maxblock,imeas),ifgfwd,ifgbwd,ifgfwd2,ifgbwd2)
    
    if (checkoutdec) then
        call tofile_ifg(trim(diagoutpath)//pathstr//'ifgfwd_'//trim(idchar)//'.dat' &
          ,min(maxifg,nifg(imeas)),ifgfwd)
        call tofile_ifg(trim(diagoutpath)//pathstr//'ifgbwd_'//trim(idchar)//'.dat' &
          ,min(maxifg,nifg(imeas)),ifgbwd)
        if (dualchandec) then
            call tofile_ifg(trim(diagoutpath)//pathstr//'ifgfwd2_'//trim(idchar)//'.dat' &
              ,min(maxifg,nifg(imeas)),ifgfwd2)
            call tofile_ifg(trim(diagoutpath)//pathstr//'ifgbwd2_'//trim(idchar)//'.dat' &
              ,min(maxifg,nifg(imeas)),ifgbwd2)    
        end if
    end if

    print *,'DC correction ...',imeas
    
    ! perform DC correction
    call DCtoACifg(DCmin,DCvar,min(maxifg,nifg(imeas)),errflag(imeas),icbfwd(imeas),cbfwd(imeas),ifgfwd & 
      ,dcmeanfwd(imeas),dcminfwd(imeas),dcmaxfwd(imeas))
    call DCtoACifg(DCmin,DCvar,min(maxifg,nifg(imeas)),errflag(imeas),icbbwd(imeas),cbbwd(imeas),ifgbwd &
      ,dcmeanbwd(imeas),dcminbwd(imeas),dcmaxbwd(imeas))
    if (errflag(imeas) .eq. 0) then
        if ((cbfwd(imeas) - cbbwd(imeas)) / (cbfwd(imeas) + cbbwd(imeas)) .gt. 0.1) &
          errflag(imeas) = errflag(imeas) + 1000
    end if
    if (errflag(imeas) .eq. 0) then
        if (abs(icbfwd(imeas) - icbbwd(imeas)) .gt. 10) errflag(imeas) = errflag(imeas) + 3000
    end if
    if (errflag(imeas) .eq. 0 .and. bandselect .eq. 1) then
        call DCtoACifg(DCmin,DCvar,min(maxifg,nifg(imeas)),errflag_CO(imeas),icbfwd2(imeas),cbfwd2(imeas),ifgfwd2 & 
          ,dcmeanfwd2(imeas),dcminfwd2(imeas),dcmaxfwd2(imeas))
        call DCtoACifg(DCmin,DCvar,min(maxifg,nifg(imeas)),errflag_CO(imeas),icbbwd2(imeas),cbbwd2(imeas),ifgbwd2 &
          ,dcmeanbwd2(imeas),dcminbwd2(imeas),dcmaxbwd2(imeas))
        if (errflag_CO(imeas) .eq. 0) then
            if ((cbfwd2(imeas) - cbbwd2(imeas)) / (cbfwd2(imeas) + cbbwd2(imeas)) .gt. 0.1) &
              errflag_CO(imeas) = errflag_CO(imeas) + 1000
        end if
        if (errflag_CO(imeas) .eq. 0) then
            if (abs(icbfwd(imeas) - icbbwd(imeas)) .gt. 10) errflag(imeas) = errflag(imeas) + 3000
        end if
    end if

    if (checkoutdec) then
        call tofile_ifg(trim(diagoutpath)//pathstr//'ifgfwdsm_'//trim(idchar)//'.dat' &
          ,min(maxifg,nifg(imeas)),ifgfwd)
        call tofile_ifg(trim(diagoutpath)//pathstr//'ifgbwdsm_'//trim(idchar)//'.dat' &
          ,min(maxifg,nifg(imeas)),ifgbwd)
        if (bandselect .eq. 1) then
            call tofile_ifg(trim(diagoutpath)//pathstr//'ifgfwdsm2_'//trim(idchar)//'.dat' &
              ,min(maxifg,nifg(imeas)),ifgfwd2)
            call tofile_ifg(trim(diagoutpath)//pathstr//'ifgbwdsm2_'//trim(idchar)//'.dat' &
              ,min(maxifg,nifg(imeas)),ifgbwd2)
        end if
    end if

    print *,'Preparing FFT ...',imeas

    ! apodization and clipping to specified OPDmax (if IFG is found to be SS, additional slope function is superimposed)
    if (errflag(imeas) .eq. 0) then
        call APOifg(min(maxifg,nifg(imeas)),icbfwd(imeas),errflag(imeas),ifgfwd,ifgfwdp)
        call APOifg(min(maxifg,nifg(imeas)),icbbwd(imeas),errflag(imeas),ifgbwd,ifgbwdp)
        if (errflag_CO(imeas) .eq. 0 .and. bandselect .eq. 1) then
            call APOifg(min(maxifg,nifg(imeas)),icbfwd2(imeas),errflag_CO(imeas),ifgfwd2,ifgfwdp2)
            call APOifg(min(maxifg,nifg(imeas)),icbbwd2(imeas),errflag_CO(imeas),ifgbwd2,ifgbwdp2)
        end if
 
        if (checkoutdec) then
            call tofile_ifg(trim(diagoutpath)//pathstr//'ifgfwdapo_'//trim(idchar)//'.dat',maxifg,ifgfwd)
            call tofile_ifg(trim(diagoutpath)//pathstr//'ifgbwdapo_'//trim(idchar)//'.dat',maxifg,ifgbwd)
            call tofile_ifg(trim(diagoutpath)//pathstr//'ifgfwdapophas_'//trim(idchar)//'.dat',maxifg,ifgfwdp)
            call tofile_ifg(trim(diagoutpath)//pathstr//'ifgbwdapophas_'//trim(idchar)//'.dat',maxifg,ifgbwdp)
            if (bandselect .eq. 1) then
                call tofile_ifg(trim(diagoutpath)//pathstr//'ifgfwdapo2_'//trim(idchar)//'.dat',maxifg,ifgfwd2)
                call tofile_ifg(trim(diagoutpath)//pathstr//'ifgbwdapo2_'//trim(idchar)//'.dat',maxifg,ifgbwd2)
                call tofile_ifg(trim(diagoutpath)//pathstr//'ifgfwdapophas2_'//trim(idchar)//'.dat',maxifg,ifgfwdp2)
                call tofile_ifg(trim(diagoutpath)//pathstr//'ifgbwdapophas2_'//trim(idchar)//'.dat',maxifg,ifgbwdp2)
            end if
        end if
    end if

    print *,'FFT ...',imeas

    ! perform FFT
    if (errflag(imeas) .eq. 0) then
        call FFTdual(ifgfwd,ifgfwdp,cspecfwd,cspecfwdp)
        call FFTdual(ifgbwd,ifgbwdp,cspecbwd,cspecbwdp)
        if (errflag_CO(imeas) .eq. 0 .and. bandselect .eq. 1) then
            call FFTdual(ifgfwd2,ifgfwdp2,cspecfwd2,cspecfwdp2)
            call FFTdual(ifgbwd2,ifgbwdp2,cspecbwd2,cspecbwdp2)
        end if
    
        if (checkoutdec) then
            call tofile_cspec(trim(diagoutpath)//pathstr//'cspecfwd_'//trim(idchar)//'.dat',maxspc,cspecfwd)
            call tofile_cspec(trim(diagoutpath)//pathstr//'cspecbwd_'//trim(idchar)//'.dat',maxspc,cspecbwd)
            call tofile_cspec(trim(diagoutpath)//pathstr//'cspecfwdphas_'//trim(idchar)//'.dat',maxspc,cspecfwdp)
            call tofile_cspec(trim(diagoutpath)//pathstr//'cspecbwdphas_'//trim(idchar)//'.dat',maxspc,cspecbwdp)
            if (bandselect .eq. 1) then
                call tofile_cspec(trim(diagoutpath)//pathstr//'cspecfwd2_'//trim(idchar)//'.dat',maxspc,cspecfwd2)
                call tofile_cspec(trim(diagoutpath)//pathstr//'cspecbwd2_'//trim(idchar)//'.dat',maxspc,cspecbwd2)
                call tofile_cspec(trim(diagoutpath)//pathstr//'cspecfwdphas2_'//trim(idchar)//'.dat',maxspc,cspecfwdp2)
                call tofile_cspec(trim(diagoutpath)//pathstr//'cspecbwdphas2_'//trim(idchar)//'.dat',maxspc,cspecbwdp2)
            end if
        end if
    end if

    ! check out-of-band artefacts   
    if (errflag(imeas) .eq. 0) then
        call checkoutofband(1,errflag(imeas),cspecfwd,cspecbwd)
        if (errflag_CO(imeas) .eq. 0 .and. bandselect .eq. 1) then
            call checkoutofband(2,errflag_CO(imeas),cspecfwd2,cspecbwd2)
        end if
    end if

    print *,'Phase correction ...',imeas

    ! perform phase correction
    if (errflag(imeas) .eq. 0 .and. anaphasdec) then
        call makeanaphase(errflag(imeas),cspecfwdp,refphas,phasfwd,anaphasfwd)
        call makeanaphase(errflag(imeas),cspecbwdp,refphas,phasbwd,anaphasbwd)
        if (errflag_CO(imeas) .eq. 0 .and. bandselect .eq. 1) then
            call makeanaphase(errflag_CO(imeas),cspecfwdp2,refphas,phasfwd2,anaphasfwd2)
            call makeanaphase(errflag_CO(imeas),cspecbwdp2,refphas,phasbwd2,anaphasbwd2)
        end if
    end if

    if (checkoutdec .and. anaphasdec) then
        call tofile_cspec(trim(diagoutpath)//pathstr//'phasfwd_'//trim(idchar)//'.dat',nphaspts,phasfwd)
        call tofile_cspec(trim(diagoutpath)//pathstr//'phasbwd_'//trim(idchar)//'.dat',nphaspts,phasbwd)
        if (bandselect .eq. 1) then
            call tofile_cspec(trim(diagoutpath)//pathstr//'phasfwd2_'//trim(idchar)//'.dat',nphaspts,phasfwd2)
            call tofile_cspec(trim(diagoutpath)//pathstr//'phasbwd2_'//trim(idchar)//'.dat',nphaspts,phasbwd2)
        end if
    end if

    if (errflag(imeas) .eq. 0) then
        call phasecorr(anaphasfwd,refphas,cspecfwd,cspecfwdp,specfwd)
        call phasecorr(anaphasbwd,refphas,cspecbwd,cspecbwdp,specbwd)
        if (reftrmdec) then
            call makereftrm(imeas,maxT,maxspc,reftrmT,reftrm)
            specfwd = specfwd / reftrm
            specbwd = specbwd / reftrm
        end if
        if (errflag_CO(imeas) .eq. 0 .and. bandselect .eq. 1) then
            call phasecorr(anaphasfwd2,refphas,cspecfwd2,cspecfwdp2,specfwd2)
            call phasecorr(anaphasbwd2,refphas,cspecbwd2,cspecbwdp2,specbwd2)
            if (reftrmdec) then
                specfwd2 = specfwd2 / reftrm
                specbwd2 = specbwd2 / reftrm
            end if
        end if

        if (checkoutdec) then
            call tofile_spec(trim(diagoutpath)//pathstr//'specfwd_'//trim(idchar)//'.dat',maxspc,specfwd)
            call tofile_spec(trim(diagoutpath)//pathstr//'specbwd_'//trim(idchar)//'.dat',maxspc,specbwd)
            if (bandselect .eq. 1) then
                call tofile_spec(trim(diagoutpath)//pathstr//'specfwd2_'//trim(idchar)//'.dat',maxspc,specfwd2)
                call tofile_spec(trim(diagoutpath)//pathstr//'specbwd2_'//trim(idchar)//'.dat',maxspc,specbwd2)
            end if
        end if
    end if

    ! check spectral calibration
    if (errflag(imeas) .eq. 0) then
        call checknuecal(1,errflag(imeas),refspec,specfwd)
        call checknuecal(1,errflag(imeas),refspec,specbwd)
        if (errflag_CO(imeas) .eq. 0 .and. bandselect .eq. 1) then
            call checknuecal(2,errflag_CO(imeas),refspec2,specfwd2)
            call checknuecal(2,errflag_CO(imeas),refspec2,specbwd2)
        end if
    end if

    ! check consistency of fwd and bwd pair of spectra
    if (errflag(imeas) .eq. 0) then
        call checkfwdbwd(1,errflag(imeas),specfwd,specbwd)
        if (errflag_CO(imeas) .eq. 0 .and. bandselect .eq. 1) then
            call checkfwdbwd(2,errflag_CO(imeas),specfwd2,specbwd2)
        end if    
    end if

    ! if both SN + SM derived from first channel ifg: copy first channel result into 2nd channel
    if (bandselect .eq. 2) then
        specfwd2 = specfwd
        specbwd2 = specbwd
        if (anaphasdec) then
            anaphasfwd2 = anaphasfwd
            anaphasbwd2 = anaphasbwd
        end if
    end if

    print *,'Spectral resampling ...',imeas

    ! perform spectral resampling, file to disc
    if (errflag(imeas) .eq. 0) then
        call resample(1,sinc,specfwd,specfwdrs)
        call resample(1,sinc,specbwd,specbwdrs)
        if (errflag_CO(imeas) .eq. 0 .and. bandselect .gt. 0) then
            call resample(2,sinc,specfwd2,specfwd2rs)
            call resample(2,sinc,specbwd2,specbwd2rs)
        end if

        if (checkoutdec) then
            call tofile_spec(trim(diagoutpath)//pathstr//'specfwdrs_'//trim(idchar)//'.dat',maxspcrs,specfwdrs)
            call tofile_spec(trim(diagoutpath)//pathstr//'specbwdrs_'//trim(idchar)//'.dat',maxspcrs,specbwdrs)
            if (bandselect .gt. 0) then
                call tofile_spec(trim(diagoutpath)//pathstr//'specfwd2rs_'//trim(idchar)//'.dat',maxspcrs,specfwd2rs)
                call tofile_spec(trim(diagoutpath)//pathstr//'specbwd2rs_'//trim(idchar)//'.dat',maxspcrs,specbwd2rs)
            end if
        end if
    end if    

    ! average fwd+bwd, write bin-file to disc
    if (errflag(imeas) .eq. 0) then
        print *,'Binary file(s) to disc ...',imeas
        specmeanrs = 0.5 * (specfwdrs + specbwdrs)
        call tofile_binspec(1,measfile(imeas),YYMMDDlocal(imeas),HHMMSSlocal(imeas) &
          ,YYMMDDUT(imeas),UTh(imeas),durationsec(imeas),astrelev(imeas),azimuth(imeas) &
          ,obslatdeg(imeas),obslondeg(imeas),obsaltkm(imeas),specmeanrs)
        if (errflag_CO(imeas) .eq. 0 .and. bandselect .gt. 0) then
            specmean2rs = 0.5 * (specfwd2rs + specbwd2rs)
            call tofile_binspec(2,measfile(imeas),YYMMDDlocal(imeas),HHMMSSlocal(imeas) &
              ,YYMMDDUT(imeas),UTh(imeas),durationsec(imeas),astrelev(imeas),azimuth(imeas) &
              ,obslatdeg(imeas),obslondeg(imeas),obsaltkm(imeas),specmean2rs)
        end if
    else
        print *,'errflag:',errflag(imeas)
        if (bandselect .gt. 0) print *,'errflag_CO:',errflag_CO(imeas)
    end if

    iunit = next_free_unit()
    open (iunit,file = logdatei,status = 'old',position = 'append')
    write (iunit,'(I7,2X,I12,2X,I12,2X,F9.5,2X,F9.4,2X,F9.4,2X,A6,2X,A6,2X,A6,2X,A,&
      &2X,F9.6,2X,F9.6,2X,F9.6,2X,F9.6,&
      &2X,F9.6,2X,F9.6,2X,F9.6,2X,F9.6,&
      &2X,F9.6,2X,F9.6,2X,F9.6,2X,F9.6,&
      &2X,F9.6,2X,F9.6,2X,F9.6,2X,F9.6)'&
    ) imeas,errflag(imeas) &
      ,errflag_CO(imeas),astrelev(imeas),azimuth(imeas),UTh(imeas),YYMMDDUT(imeas),YYMMDDlocal(imeas) &
      ,HHMMSSlocal(imeas),trim(measfile(imeas)), &
      dcmeanfwd(imeas),dcminfwd(imeas),dcmaxfwd(imeas),((dcmaxfwd(imeas)/dcminfwd(imeas))-1.0), & 
      dcmeanbwd(imeas),dcminbwd(imeas),dcmaxbwd(imeas),((dcmaxbwd(imeas)/dcminbwd(imeas))-1.0), &
      dcmeanfwd2(imeas),dcminfwd2(imeas),dcmaxfwd2(imeas),((dcmaxfwd2(imeas)/dcminfwd2(imeas))-1.0), &
      dcmeanbwd2(imeas),dcminbwd2(imeas),dcmaxbwd2(imeas),((dcmaxbwd2(imeas)/dcminbwd2(imeas))-1.0)
    close (iunit)

end do

! deallocate arrays of parallel loop
deallocate (specmeanrs,specmean2rs)
deallocate (specfwdrs,specbwdrs,specfwd2rs,specbwd2rs)
deallocate (specfwd,specbwd,specfwd2,specbwd2)
deallocate (cspecfwdp,cspecbwdp,cspecfwdp2,cspecbwdp2)
deallocate (cspecfwd,cspecbwd,cspecfwd2,cspecbwd2)
deallocate (ifgfwdp,ifgbwdp,ifgfwdp2,ifgbwdp2)
deallocate (ifgfwd,ifgbwd,ifgfwd2,ifgbwd2)
deallocate (phasfwd,phasbwd,phasfwd2,phasbwd2)
deallocate (anaphasfwd,anaphasbwd,anaphasfwd2,anaphasbwd2)

!====================================================================
!  Deallocation of general arrays
!====================================================================
if (reftrmdec) deallocate (reftrmT)
deallocate (refspec,refspec2,refphas,reftrm)
deallocate (sinc)

deallocate (JDdate,UTh,durationsec,astrelev,azimuth)
deallocate (YYMMDDlocal,HHMMSSlocal,YYMMDDUT)
deallocate (obslatdeg,obslondeg,obsaltkm)
deallocate (cbfwd,cbbwd,cbfwd2,cbbwd2)

deallocate (blocktype,blocklength,blockptr)
deallocate (measfile,nptrfirstdir,nofblock,nifg)
deallocate (icbfwd,icbbwd,icbfwd2,icbbwd2)
deallocate (errflag,errflag_CO)

! added by Moritz Makowski to perform the DC min / DC var filtering in retrospective
deallocate (dcmeanfwd,dcmeanbwd,dcmeanfwd2,dcmeanbwd2)
deallocate (dcminfwd,dcminbwd,dcminfwd2,dcminbwd2)
deallocate (dcmaxfwd,dcmaxbwd,dcmaxfwd2,dcmaxbwd2)

end program preprocess6











!====================================================================
!  APOifg
!====================================================================
subroutine APOifg(nifg,icb,errflag,ifg,ifgphas)

use glob_prepro6,only : pi,maxifg,ifgradius,nphaspts

implicit none

integer,intent(in) :: nifg,icb
integer(8),intent(inout) :: errflag
real,dimension(maxifg),intent(inout) :: ifg
real,dimension(maxifg),intent(out) :: ifgphas

integer :: i,iramp
real :: xwert,term,apowert,norm
real,dimension(:), allocatable :: wrkifg,wrkifgphas

! Enough ifg points available on one side of the ifg for requested resolution?
if (.not. (icb .gt. ifgradius .or. (nifg - icb) .gt. ifgradius)) then
    errflag = errflag + 10000
    call warnout("Insuff IFG pts for requested resolution!",0)
    return
end if

! Enough points available for calculating phase spectrum?
if (.not. (icb .gt. nphaspts .and. (nifg - icb) .gt. nphaspts)) then
    errflag = errflag + 1000000
    call warnout("Insuff phase resolution!",0)
    return
end if

allocate (wrkifg(maxifg),wrkifgphas(maxifg))
wrkifg = ifg
wrkifgphas = ifg
ifg = 0.0
ifgphas = 0.0

! set IFG values to zero outside OPDmax (this works for DS and SS IFGs)
do i = 1,icb - ifgradius - 1
    wrkifg(i) = 0.0
end do
do i = icb + ifgradius + 1,maxifg
    wrkifg(i) = 0.0
end do

! set IFG values to zero outside phase window (this works for DS and SS IFGs)
do i = 1,icb - nphaspts - 1
    wrkifgphas(i) = 0.0
end do
do i = icb + nphaspts + 1,maxifg
    wrkifgphas(i) = 0.0
end do

! NBM apodization on wrkifg
do i = 1,maxifg
    xwert = real(i - icb) / real(ifgradius)
    term = (1.0 - xwert * xwert)
    apowert = 0.152442 - 0.136176 * term + 0.983734 * term * term
    wrkifg(i) = wrkifg(i) * apowert
end do

! cos apodization on wrkifgphas
do i = icb - nphaspts,icb + nphaspts
    xwert = real(pi) * real(i - icb) / real(nphaspts)
    wrkifgphas(i) = wrkifgphas(i) * 0.5 * (cos(xwert) + 1.0)
end do

! If SS ifg:
! for SS points: x2
! for DS points: linear rise

if (icb .lt. ifgradius + 1) then ! SS IFG, left side short
    iramp = 2 * (icb - 1) + 1
    norm = 2.0 / real(iramp - 1)
    do i = 1,iramp
        wrkifg(i) = wrkifg(i) * norm * real(i - 1)
    end do
    do i = iramp + 1,nifg
        wrkifg(i) = 2.0 * wrkifg(i)
    end do
end if

if (icb .gt. nifg - ifgradius - 1) then ! SS IFG, right side short
    iramp = 2 * (nifg - icb) + 1
    norm = 2.0 / real(iramp - 1)
    do i = 1,nifg - iramp
        wrkifg(i) = 2.0 * wrkifg(i)
    end do
    do i = nifg - iramp + 1,nifg
        wrkifg(i) = wrkifg(i) * norm * real(nifg - i)
    end do
end if

! resort arrays for FFT
ifg(1) = wrkifg(icb)
do i = 1,min(ifgradius,icb - 1)
    ifg(i+1) = wrkifg(icb-i)
end do
do i = 1,min(ifgradius,nifg - icb)
    ifg(maxifg-i+1) = wrkifg(icb+i)
end do

ifgphas(1) = wrkifgphas(icb)
do i = 1,nphaspts
    ifgphas(i+1) = wrkifgphas(icb-i)
end do
do i = 1,nphaspts
    ifgphas(maxifg-i+1) = wrkifgphas(icb+i)
end do

deallocate (wrkifg,wrkifgphas)

end subroutine APOifg



!====================================================================
!  calcsolpos
!====================================================================
subroutine calcsolpos(imeas,nifg,latdeg,londeg,JDdate,YYMMDDlocal,HHMMSSlocal,YYMMDDUT &
  ,UTh,durationsec,astrelevdeg,azimuthdeg)

use glob_prepro6, only : gradtorad,radtograd,toffseth_UT
use glob_OPUSparms6

implicit none

integer,intent(in) :: imeas,nifg
real,intent(in) :: latdeg,londeg
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
! determine scan duration (EM27/SUN DS IFG has 113747 points)
! read(OPUS_parms(imeas)%VEL,*) velocity
! durationsec = 58.32 * 8.79144e-6 * real(OPUS_parms(imeas)%NSS) * real(nifg) / velocity
durationsec = OPUS_parms(imeas)%DUR 

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
laengerad = -gradtorad * londeg
breiterad = gradtorad * latdeg
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

    use glob_prepro6, only : gradtorad

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

    use glob_prepro6, only : gradtorad

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

use glob_prepro6,only : maxspc,nuelas

implicit none

integer,intent(in) :: ichan
integer(8),intent(inout) :: errflag
real,dimension(maxspc),intent(in) :: specfwd,specbwd

real(8),parameter :: nuesiglow1 = 5544.0d0
real(8),parameter :: nuesighigh1 = 12053.0d0
real(8),parameter :: nuesiglow2 = 4098.0d0
real(8),parameter :: nuesighigh2 = 5062.0d0
real(8),parameter :: schwelle1 = 0.01d0
real(8),parameter :: schwelle2 = 0.01d0

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
    diffwert = diffwert + abs(specfwd(i) - ratio * specbwd(i))
end do
diffwert = 0.5d0 * diffwert / ((sigfwd + sigbwd) * real(isighigh - isiglow + 1,8))

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

use glob_prepro6,only : maxspc,nuelas

implicit none

integer,intent(in) :: ichan
integer(8),intent(inout) :: errflag
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

use glob_prepro6, only : dualchandec,OPDmax
use glob_OPUSparms6

implicit none

character(len=*),intent(in) :: measfile
integer,intent(in) :: imeas

if (OPUS_parms(imeas)%RES .gt. 0.90001d0 / OPDmax) then
    print *,measfile
    print *,'OPUS RES:',OPUS_parms(imeas)%RES
    print *,'Requested RES:',0.9d0 / OPDmax
    call warnout ('RES too small!',0)
end if

if (modulo(OPUS_parms(imeas)%NSS,2) .gt. 0) then
    print *,measfile
    call warnout ('Uneven number of scans!',1)    
end if

!!!if (scan(OPUS_parms(imeas)%AQM,"DD") .lt. 1) then
!!!    print *,measfile
!!!    call warnout ('IFG not double-sided!',0)
!!!end if

end subroutine checkOPUSparms



!====================================================================
!  checkoutofband
!====================================================================
subroutine checkoutofband(ichan,errflag,cspecfwd,cspecbwd)

use glob_prepro6,only : maxspc,nuelas

implicit none

integer,intent(in) :: ichan
integer(8),intent(inout) :: errflag
complex,dimension(maxspc) :: cspecfwd,cspecbwd

real(8),parameter :: nuesiglow1 = 5544.0d0
real(8),parameter :: nuesighigh1 = 12535.0d0
real(8),parameter :: nueofflow1 = 964.0d0
real(8),parameter :: nueoffhigh1 = 3850.0d0 !4339.0d0
real(8),parameter :: schwelle1 = 0.01

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
subroutine DCtoACifg(DCmin,DCvar,nifg,errflag,icb,cbamp,ifg,dcmean_record,dcmin_record,dcmax_record)

use glob_prepro6,only : maxifg,nsmooth

implicit none

real,intent(in) :: DCmin,DCvar
integer,intent(in) :: nifg
integer(8),intent(inout) :: errflag
integer,intent(out) :: icb
real,intent(out) :: cbamp
real,dimension(maxifg),intent(inout) :: ifg

real,intent(out) :: dcmean_record,dcmin_record,dcmax_record

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

dcmean_record = mean
dcmin_record = minwert
dcmax_record = maxwert


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

use glob_prepro6,only : mpowFFT,maxifg,maxspc,pi

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
!  FFTdual
!====================================================================
subroutine FFTdual(ifg,ifgb,spec,specb)

use glob_prepro6,only : mpowFFT,maxifg,maxspc,pi

implicit none

real,dimension(maxifg),intent(in) :: ifg,ifgb
complex,dimension(maxspc),intent(out) :: spec,specb

integer :: i,j,k,l,n1,n2
real(8) :: angle,argument,c,s,xdum,ydum,xbdum,ybdum
real(8),dimension(:),allocatable :: x,y,xb,yb

allocate(x(maxifg),y(maxifg),xb(maxifg),yb(maxifg))

do i = 1,maxifg
    x(i) = real(ifg(i),8)
    xb(i) = real(ifgb(i),8)
end do
y = 0.0d0
yb = 0.0d0

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

            xbdum = xb(i+1) - xb(l+1)
            xb(i+1) = xb(i+1) + xb(l+1)
            ybdum = yb(i+1) - yb(l+1)
            yb(i+1) = yb(i+1) + yb(l+1)
            xb(l+1) = xbdum * c - ybdum * s
            yb(l+1) = ybdum * c + xbdum * s

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

        xbdum = xb(j+1)
        xb(j+1) = xb(i+1)
        xb(i+1) = xbdum
        ybdum = yb(j+1)
        yb(j+1) = yb(i+1)
        yb(i+1) = ybdum

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
    specb(i) = cmplx(xb(i),yb(i))
end do

deallocate (x,y,xb,yb)

end subroutine FFTdual



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
!  makeanaphase
!====================================================================
subroutine makeanaphase(errflag,cspec,refphase,phastest,anaphas)

use glob_prepro6,only : maxspc,nphaspts,nphasrim,nphas

implicit none

integer(8),intent(inout) :: errflag
complex,dimension(maxspc),intent(in) :: cspec
real,dimension(maxspc),intent(in) :: refphase
complex,dimension(nphaspts),intent(out) :: phastest
real(8),dimension(nphas),intent(out) :: anaphas

real,parameter :: phascut = 0.05
real(8),parameter :: epsreg = 1.0d-9

integer :: i,j,k,iref,irefact,icount
real(8) :: samplingratio,xj,wert,xwert,phaswert,phaserr,norm
real :: weightmax,xrest

complex,dimension(:),allocatable :: cspecrs
real(8),dimension(:),allocatable :: refphasers
real(8),dimension(:,:),allocatable :: jak,jTj,jTjinv
real(8),dimension(:),allocatable :: jTphas
real,dimension(:),allocatable :: weight,phase

allocate (cspecrs(nphaspts),weight(nphaspts),refphasers(nphaspts),phase(nphaspts))
allocate (jak(nphaspts,nphas),jTphas(nphas),jTj(nphas,nphas),jTjinv(nphas,nphas))
cspecrs = (0.0,0.0)
refphasers = 0.0
jak = 0.0d0
weight = 0.0
phase = 0.0

! resample oversampled phase spectrum to much coarser grid
samplingratio = real(maxspc - 1,8) / real(nphaspts - 1,8)
do i = 1 + nphasrim,nphaspts - nphasrim
    xj = 1 + real(i - 1,8) * samplingratio
    j = int(xj)
    xrest = real(xj - real(j,8))
    cspecrs(i) = (1.0 - xrest) * cspec(j) + xrest * cspec(j+1)
    refphasers(i) = (1.0 - xrest) * refphase(j) + xrest * refphase(j+1)
end do

! set weights for phase fit (amplitude of complex pointer in resampled spectrum)
! find spectral reference point in resampled spectrum (maximal intensity) 
weightmax = 0.0
iref = 0
do i = 1 + nphasrim,nphaspts - nphasrim
    weight(i) = sqrt(abs(cspecrs(i)))
    if (weight(i) .gt. weightmax) then
        weightmax = weight(i)
        iref = i
    end if
end do

! determine phase spectrum on resampled grid (go to right / to left from reference point)
! set weights below threshold to zero
phase(iref) = atan2(aimag(cspecrs(iref)),real(cspecrs(iref))) !winkelzuxy(cspecrs(iref))

! from reference point to higher wavenumbers
irefact = iref
do i = iref + 1,nphaspts - nphasrim
    if (weight(i) .gt. phascut * weightmax) then
        phase(i) = phase(irefact) + dphase(cspecrs(i),cspecrs(irefact))
        irefact = i
    else
        weight(i) = 0.0
        phase(i) = 0.0
    end if
end do

! from reference point to lower wavenumbers
irefact = iref
do i = iref - 1,1 + nphasrim,-1
    if (weight(i) .gt. phascut * weightmax) then
        phase(i) = phase(irefact) + dphase(cspecrs(i),cspecrs(irefact))
        irefact = i
    else
        weight(i) = 0.0
        phase(i) = 0.0
    end if 
end do

! determine polynomial coeffs for analytical phase spectrum
! calculate weighted Jacobean (nue range 0 ... nuelas mapped onto 0 ... 2)
norm = 2.0d0 / real(nphaspts - 1,8)
do i = 1 + nphasrim,nphaspts - nphasrim
    xwert = norm * real(i - 1,8)
    wert = xwert
    jak(i,1) = real(weight(i),8)
    do j = 2,nphas
        jak(i,j) = real(weight(i),8) * wert
        wert = wert * xwert
    end do
end do
    
! calculate jTphas
do i = 1,nphas
    wert = 0.0d0
    do j = 1 + nphasrim,nphaspts - nphasrim
        wert = wert + jak(j,i) * real(weight(j) * (phase(j) - refphasers(j)),8)
    end do
    jTphas(i) = wert
end do

! calculate jTj
do i = 1,nphas
    do j = 1,nphas
        wert = 0.0d0
        do k = 1 + nphasrim,nphaspts - nphasrim
            wert = wert + jak(k,i) * jak(k,j)
        end do
        jTj(i,j) = wert
    end do
end do

! regularization
do i = 1,nphas
    jTj(i,i) = (1.0d0 + epsreg) * jTj(i,i)
end do

! matrix inversion
call matinvers(nphas,jTj,jTjinv)

! calculate polynomial phase parameters
do i = 1,nphas
    wert = 0.0d0
    do j = 1,nphas
        wert = wert + jTjinv(j,i) * jTphas(j)
    end do
    anaphas(i) = wert
end do

! check quality of analytical phase
phastest = 0.0
icount = 0
phaserr = 0.0d0
norm = 2.0d0 / real(nphaspts - 1,8)
do i = 1 + nphasrim,nphaspts - nphasrim
    xwert = norm * real(i - 1,8)
    wert = xwert
    phaswert = anaphas(1)
    do j = 2,nphas
        phaswert = phaswert + anaphas(j) * wert
        wert = wert * xwert
    end do
    phaswert = phaswert + refphasers(i)
    phastest(i) = cmplx(real(phase(i)),real(phaswert))
    if (weight(i) .gt. phascut * weightmax) then
        icount = icount + 1
        phaserr = phaserr + abs(real(cspecrs(i)) * sin(phaswert) - aimag(cspecrs(i)) &
          * cos(phaswert)) / weight(i)
    end if       
end do
phaserr = phaserr / real(icount,8)

print *,'phase fit quality: ',phaserr
if (phaserr .gt. 0.005) then
    errflag = errflag + 1000000000
end if

deallocate (jak,jTphas,jTj,jTjinv)
deallocate (cspecrs,weight,refphasers,phase)

contains

    !====================================================================
    !  function dphase
    !====================================================================
    real function dphase(cwert,cwertref)

    implicit none

    complex,intent(in) :: cwert,cwertref

    real :: norm,normref,cross

    norm = abs(cwert)
    normref = abs(cwertref)
    cross = (real(cwertref) * aimag(cwert) - aimag(cwertref) * real(cwert)) / (norm * normref)
    dphase = asin(cross)     

    end function dphase

end subroutine makeanaphase



!====================================================================
!  makereftrm: calculates T dependent transmission
!====================================================================
subroutine makereftrm(imeas,maxT,maxspc,reftrmT,reftrm)

use glob_OPUSparms6

implicit none

integer,intent(in) :: imeas,maxT,maxspc 
real,dimension(maxT,maxspc),intent(in) :: reftrmT
real,dimension(maxspc),intent(out) :: reftrm

integer :: i,iwert
real :: rest
real(8) :: xwert

xwert = (OPUS_parms(imeas)%TSC + 2.0d0) / 2.0d0

if (xwert .lt. 1.0001d0) xwert = 1.0001d0
if (xwert .gt. 28.9999d0) xwert = 28.9999d0

iwert = int(xwert)
rest = real(xwert - real(iwert,8))

do i = 1,maxspc
    reftrm(i) = (1.0 - rest) * reftrmT(iwert,i) + rest * reftrmT(iwert+1,i)
end do

end subroutine makereftrm



!====================================================================
!  matinvers: invertiert eine symmetrische nmax x nmax Matrix
!====================================================================
subroutine matinvers(nmax,matein,mataus)

implicit none

integer,intent(in) :: nmax
real(8),dimension(nmax,nmax),intent(in) :: matein
real(8),dimension(nmax,nmax),intent(out) :: mataus

logical :: warnung
logical,dimension(nmax):: done
integer :: i,j,k,l,jj,kk,jk,lk,nrank,nvmax,icount
real(8) :: check
real(16) :: vkk,vjk,pivot
real(16),dimension(:),allocatable :: v

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
    call warnout('inverted matrix incorrect!',1)
end if

end subroutine matinvers



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

use glob_prepro6,only : maxOPUSchar

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
subroutine phasecorr(anaphase,refphase,cspec,cspecp,spec)

use glob_prepro6,only : maxspc,nphas,anaphasdec

implicit none

real(8),dimension(nphas),intent(in) :: anaphase
real,dimension(maxspc),intent(in) :: refphase
complex,dimension(maxspc),intent(in) :: cspec,cspecp
real,dimension(maxspc),intent(out) :: spec

integer :: i,j
real(8) :: xnorm,xwert,wert,phase
real :: normp

if (anaphasdec) then
    xnorm = 2.0d0 / real(maxspc - 1,8)
    do i = 1,maxspc
        xwert = xnorm * real(i - 1,8)
        wert = xwert
        phase = anaphase(1)
        do j = 2,nphas
            phase = phase + anaphase(j) * wert
            wert = wert * xwert
        end do
        phase = phase + real(refphase(i),8)
        spec(i) = real(cspec(i)) * cos(phase) + aimag(cspec(i)) * sin(phase)
    end do
else
    do i = 1,maxspc
        normp = sqrt(real(cspecp(i)) * real(cspecp(i)) + aimag(cspecp(i)) * aimag(cspecp(i)))
        spec(i) = (real(cspec(i)) * real(cspecp(i)) + aimag(cspec(i)) * aimag(cspecp(i))) / (normp + 1.0e-25)
    end do
end if

end subroutine phasecorr



!====================================================================
!  prepare_sinc
!====================================================================
subroutine prepare_sinc(sinc)

use glob_prepro6, only : nconv,nzf,nsinc,pi

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
subroutine read_ifg(nofblock,nifg,measfile,blocktype,blockptr &
  ,ifgfwd,ifgbwd,ifgfwd2,ifgbwd2)

use glob_prepro6, only : maxblock,maxifg,dualchandec,chanswapdec

implicit none

integer,intent(in) :: nofblock,nifg
character(len=*),intent(in) :: measfile
integer,dimension(maxblock),intent(in) :: blocktype,blockptr
real,dimension(maxifg),intent(out) :: ifgfwd,ifgbwd,ifgfwd2,ifgbwd2

integer :: i,iunit,iowert,ptrifg,ptrifg2,nrest,next_free_unit
real,dimension(:),allocatable :: wrkifg

if (nifg .gt. maxifg) then
    nrest = 2 * (nifg - maxifg)
    allocate (wrkifg(nrest))
end if

ifgfwd = 0.0
ifgbwd = 0.0
ifgfwd2 = 0.0
ifgbwd2 = 0.0

ptrifg = -9999
ptrifg2 = -9999
do i = 1,nofblock
   if (blocktype(i) .eq. 2055) then
        ptrifg = blockptr(i)
    end if
    if (blocktype(i) .eq. 34823) then
        ptrifg2 = blockptr(i)
    end if
end do
if (dualchandec) then
    if (ptrifg .eq. -9999 .or. ptrifg2 .eq. -9999) then
        call warnout('OPUS file: only one channel!',0)
    end if
else
    if (ptrifg .eq. -9999) then
        call warnout('OPUS file: missing ifg pointer!',0)
    end if
end if

iunit = next_free_unit()

open (iunit,file = trim(measfile),form='unformatted',access ='stream',status = 'old',action = 'read',iostat = iowert)

if (iowert .ne. 0) then
    print *,trim(measfile)
    call warnout('Cannot open measurement file!',0)
end if

if (chanswapdec) then
    read(unit = iunit,pos = ptrifg + 1) ifgfwd2(1:min(maxifg,nifg))
    if (nifg .gt. maxifg) then
        read(unit = iunit) wrkifg(1:nrest)
    end if    
    do i = min(maxifg,nifg),1,-1
        read(unit = iunit) ifgbwd2(i)
    end do
    read(unit = iunit,pos = ptrifg2 + 1) ifgfwd(1:min(maxifg,nifg))
    if (nifg .gt. maxifg) then
        read(unit = iunit) wrkifg(1:nrest)
    end if
    do i = min(maxifg,nifg),1,-1
        read(unit = iunit) ifgbwd(i)
    end do
else
    read(unit = iunit,pos = ptrifg + 1) ifgfwd(1:min(maxifg,nifg))
    if (nifg .gt. maxifg) then
        read(unit = iunit) wrkifg(1:nrest)
    end if
    do i = min(maxifg,nifg),1,-1
        read(unit = iunit) ifgbwd(i)
    end do
    if (dualchandec) then
        read(unit = iunit,pos = ptrifg2 + 1) ifgfwd2(1:min(maxifg,nifg))
        if (nifg .gt. maxifg) then
            read(unit = iunit) wrkifg(1:nrest)
        end if
        do i = min(maxifg,nifg),1,-1
            read(unit = iunit) ifgbwd2(i)
        end do
    end if
end if

close (iunit)

if (nifg .gt. maxifg) then
    deallocate (wrkifg)
end if

end subroutine read_ifg



!====================================================================
!  read_input: Einlesen der Eingabedatei
!====================================================================
subroutine read_input(inpdatei)

use glob_prepro6

implicit none

character(len=*),intent(in) :: inpdatei

character(len = lengthcharmeas) :: zeile,dateiname
logical :: marke,decfileda,decsize
integer :: iunit,iowert,imeas,next_free_unit,nfilebytes,iscan

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
read(iunit,*) semiFOV

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
read(iunit,'(L)') dualchandec
read(iunit,'(L)') chanswapdec
read(iunit,'(L)') anaphasdec
read(iunit,'(I2)') bandselect

if (diagoutpath .eq. 'standard') diagoutpath = 'diagnosis'
if (chanswapdec .and. .not. dualchandec) call warnout('chanswap requires dualchandec',0)
if (bandselect .eq. 1 .and. .not. dualchandec) call warnout('bandselect = 1 requires dualchandec',0)

call gonext(iunit,.false.)
read(iunit,'(A)') infotext

call gonext(iunit,.false.)
! determine number of raw measurements to treat
marke = .false.
imeas = 0
do while (.not. marke)
    zeile = ''
    read(iunit,'(A)') zeile
    if (zeile(1:3) .eq. '***') then
        marke = .true.
    else        
        ! test OPSUS file existence and size here
        if (obsfixdec) then
            dateiname = trim(zeile)
        else
            iscan = scan(zeile,',')
            dateiname = zeile(1:iscan - 1)
        end if
        inquire(file = trim(dateiname),exist = decfileda,size = nfilebytes)
        if (.not. decfileda) then
            print *,dateiname
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
subroutine read_meas_files(inpdatei,nmeas,measfile,obslatdeg,obslondeg,obsaltkm)

use glob_prepro6, only : obsfixdec,obsfixlatdeg,obsfixlondeg,obsfixaltkm,lengthcharmeas,minfilesize

implicit none

character(len=*),intent(in) :: inpdatei
integer,intent(in) :: nmeas
character(len=lengthcharmeas),dimension(nmeas),intent(out) :: measfile
real,dimension(nmeas),intent(out) :: obslatdeg,obslondeg,obsaltkm

logical :: marke,decfileda,decsize
character(len=lengthcharmeas) :: zeile,dateiname
integer :: i,imeas,imeasall,iunit,iowert,next_free_unit,nfilebytes,iscan
real :: latdeg,londeg,altkm

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
    zeile = ''
    read(iunit,'(A)') zeile
    if (zeile(1:3) .ne. '***') then
        if (obsfixdec) then
            dateiname = trim(zeile)
            latdeg = obsfixlatdeg
            londeg = obsfixlondeg
            altkm = obsfixaltkm
        else
            iscan = scan(zeile,',')
            dateiname = zeile(1:iscan - 1)
            read(zeile(iscan+1:len(trim(zeile))),*) latdeg,londeg,altkm
        end if
    end if
    if (zeile(1:3) .eq. '***') then
        marke = .true.
    else        
        ! test file size here
        inquire(file = trim(dateiname),exist = decfileda,size = nfilebytes)
        if (.not. decfileda) then
            print *,dateiname
            call warnout('spectrum file does not exist!',0)
        end if
        if (nfilebytes .lt. minfilesize) then
            decsize = .false.
        else
            decsize = .true.
        end if
        if (decsize) then
            imeas = imeas + 1
            obslatdeg(imeas) = latdeg
            obslondeg(imeas) = londeg
            obsaltkm(imeas) = altkm
            measfile(imeas) = trim(dateiname)
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
  ,blocklength,blockptr,nifg)

use glob_prepro6,only : maxblock,maxblength,maxifg,dualchandec,ifgradius,nphaspts

implicit none

character(len=*),intent(in) :: measfile
integer,intent(in) :: nptrfirstdir,nofblock
integer,dimension(maxblock),intent(out) :: blocktype,blocklength,blockptr
integer,intent(out) :: nifg

character(len=1) :: charbyte
logical :: dualifg
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

if (dualifg .neqv. dualchandec) then
    print *,measfile
    call warnout ('inconsistent dualifg!',0)    
end if

if (nifga .eq. 0) then
    print *,measfile
    call warnout('Zero IFG block size!',0)
end if

if (dualchandec .and. nifga .ne. nifgb) then
    print *,measfile
    call warnout('Differing sizes of dual channel IFGs!',0)
else
    if (mod(nifga,8) .ne. 0) then
        print*, measfile
        call warnout('Unexpected IFG size!',0)
    end if
    nifg = nifga / 8
end if

if (nifg .gt. maxifg) then
    print *,measfile
    call warnout('Note: nifg > maxifg',1)
end if

if (nifg .lt. ifgradius + nphaspts + 1) then
    print *,measfile
    call warnout('IFG size too small!',0)
end if

end subroutine read_opus_dir



!====================================================================
!  read_opus_hdr
!====================================================================
subroutine read_opus_hdr(measfile,nptrfirstdir,nofblock)

use glob_prepro6, only : maxblock

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

use glob_prepro6,only : maxblock,maxblength
use glob_OPUSparms6

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
call OPUS_eval_dble(blocklength(i),binchar,'DUR',OPUS_parms(imeas)%DUR)

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

integer :: i,icount,ixpos,iunit,iowert,next_free_unit
real :: wert
real(8) :: a0,a1,a2,a3,a4,xpos,rest,gridratio
real,dimension(:),allocatable :: wrkspec

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

if (icount .lt. maxspc) then
    print *,'maxspc:',maxspc
    print *,'icount:',icount
    call warnout('Incompatible # of entries in refspec!',0)
end if

iunit = next_free_unit()
open (iunit,file = trim(refspecfile),status = 'old',iostat = iowert)
if (icount .gt. maxspc) then
    allocate (wrkspec(icount))    
    do i = 1,icount
        read(iunit,*) wrkspec(i)
    end do
    close (iunit)
    ! interpolation on output grid
    gridratio = real(icount - 1,8) / real(maxspc - 1,8)
    refspec(1) = wrkspec(1)
    xpos = 1.0d0 + gridratio
    ixpos = nint(xpos)
    rest = xpos - real(ixpos,8)
    a0 = wrkspec(ixpos)
    a1 = 0.5d0 * (wrkspec(ixpos + 1) - wrkspec(ixpos - 1))
    a2 = 0.125d0 * (wrkspec(ixpos-1) - 2.0d0 * wrkspec(ixpos) + wrkspec(ixpos+1))
    refspec(2) = a0 + rest * (a1 + rest * a2)
    do i = 3,maxspc - 2
        xpos = 1.0d0 + gridratio * real(i - 1,8)
        ixpos = nint(xpos)
        rest = xpos - real(ixpos,8)
        a0 = wrkspec(ixpos)
        a1 = wrkspec(ixpos - 2) / 12.0d0 - 2.0d0 * wrkspec(ixpos - 1) &
          / 3.0d0 + 2.0d0 * wrkspec(ixpos + 1) / 3.0d0 - wrkspec(ixpos + 2) / 12.0d0
        a2 = - wrkspec(ixpos - 2) / 24.0d0 + 2.0d0 * wrkspec(ixpos - 1) / 3.0d0 - 5.0d0 * wrkspec(ixpos) / 4.0d0 &
          + 2.0d0 * wrkspec(ixpos + 1) / 3.0d0 - wrkspec(ixpos + 2) / 24.0d0
        a3 = - wrkspec(ixpos - 2) / 12.0d0 + wrkspec(ixpos - 1) / 6.0d0 - wrkspec(ixpos + 1) / 6.0d0 &
          + wrkspec(ixpos + 2) / 12.0d0
        a4 = wrkspec(ixpos - 2) / 24.0d0 - wrkspec(ixpos - 1) / 6.0d0 + 0.25d0 * wrkspec(ixpos) - wrkspec(ixpos + 1) &
          / 6.0d0 + wrkspec(ixpos + 2) / 24.0d0
        refspec(i) = a0 + rest * (a1 + rest * (a2 + rest * (a3 + rest * a4)))
    end do
    xpos = 1.0d0 + gridratio * real(maxspc - 2,8)
    ixpos = nint(xpos)
    rest = xpos - real(ixpos,8)
    a0 = wrkspec(ixpos)
    a1 = 0.5d0 * (wrkspec(ixpos + 1) - wrkspec(ixpos - 1))
    a2 = 0.125d0 * (wrkspec(ixpos-1) - 2.0d0 * wrkspec(ixpos) + wrkspec(ixpos+1))
    refspec(maxspc - 1) = a0 + rest * (a1 + rest * a2)
    refspec(maxspc) = wrkspec(icount)
    deallocate (wrkspec)
else
    do i = 1,icount
        read(iunit,*) refspec(i)
    end do
    close (iunit)
end if

end subroutine read_refspec



!====================================================================
!  read_reftrmT
!====================================================================
subroutine read_reftrmT(refspecfile,maxT,maxspc,reftrmT)

implicit none

character(len=*),intent(in) :: refspecfile
integer,intent(in) :: maxT,maxspc
real,dimension(maxT,maxspc),intent(out) :: reftrmT

character(len=376) :: zeile
integer :: i,j,icount,iunit,iowert,next_free_unit

iunit = next_free_unit()
! check availability of file, number of file entries
open (iunit,file = trim(refspecfile),status = 'old',iostat = iowert)

if (iowert .ne. 0) then
    print *,trim(refspecfile)
    call warnout('Cannot open refspec file!',0)
end if

icount = 0
do
    read(iunit,'(A376)',end = 102) zeile
    icount = icount + 1
end do
102 continue
close (iunit)

if (icount .ne. maxspc) then
    print *,'maxspc:',maxspc
    print *,'icount:',icount
    call warnout('Incompatible # of entries in reftrmT!',0)
end if

iunit = next_free_unit()
open (iunit,file = trim(refspecfile),status = 'old',iostat = iowert)  
do i = 1,maxspc
    read(iunit,'(A376)') zeile
    read (zeile,'(E12.5,28(1X,E12.5))') (reftrmT(j,i),j = 1,maxT)
end do
close (iunit)

end subroutine read_reftrmT



!====================================================================
!  resample
!====================================================================
subroutine resample(ichan,sinc,spec,specrs)

use glob_prepro6, only : maxspc,maxspcrs,nsinc,nzf,nconv &
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

use glob_prepro6, only : maxspc,maxspcrs,nsinc,nconv,nuelas,pi,OPDmax &
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
!  tofile_binspec
!====================================================================
subroutine tofile_binspec(ichan,measfile,YYMMDDlocal,HHMMSSlocal,YYMMDDUT &
  ,UTh,durationsec,astrelev,azimuth,latdeg,londeg,altkm,spec)

use glob_prepro6

implicit none

integer,intent(in) :: ichan
character(len=*),intent(in) :: measfile
character(len=6),intent(in) :: YYMMDDlocal,HHMMSSlocal,YYMMDDUT
real,intent(in) :: UTh,durationsec,astrelev,azimuth,latdeg,londeg,altkm
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
write (numchar,'(F10.5)') latdeg
write (iunit) trim(numchar),eol
numchar = '              '
write (numchar,'(F10.5)') londeg
write (iunit) trim(numchar),eol
numchar = '              '
write (numchar,'(F9.5)') altkm
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
use glob_prepro6, only : quietrundec

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
