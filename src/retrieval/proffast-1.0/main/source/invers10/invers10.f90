!     Last change:  BLA   8 Jul 2018    5:02 pm

!====================================================================
!
! This code has been developed for use with COCCON spectrometers
! by Frank Hase, KIT (frank.hase@kit.edu). It retrieves column-averaged
! trace gas abundances from spectra generated with the COCCON-PROCEEDS
! preprocessor. It uses daily precalculated x-sections provided by "pcxs".
! (pcxs has to be executed before this code is started)
!
!====================================================================

program invers10

use globinv10

implicit none

logical :: convergdec,sampdec,inverfolg,dateidadec
character(len=2) :: exta
character(len=300) :: inputdatei
character(len=300) :: filename
character(len=12) :: specname2
integer :: i,j,k,l,ndpTdt,ipTptr,nderi,icount,iiter,iowert,iunit_dtmess,next_free_unit
real :: dp,dT,sollnorm,nueskalfaktor,dtmess,give_rms,damping,dpmean,LMstab,largest_EVal
real(8) :: solskal,centernue,refraction_rad

integer,dimension(maxjob) :: iunit_specout
character(len=6),dimension(:),allocatable :: HHMMSSdpTdt 
real(8),dimension(:),allocatable :: totcol_ref
real,dimension(:),allocatable :: dpdt,dTdt
real,dimension(:),allocatable :: solspec_ref,solspec,fullmesspec,trm,wrkisa
real,dimension(:),allocatable :: basexils,specxils,messxils,dspecxilsdnue &
  ,weightxils,dparm
real,dimension(:,:),allocatable :: ils,wrktau,jak,jtj,jtj_inv
real,dimension(:,:),allocatable :: dspecxilsdcol,dwrkxilsdbase,dspecxilsdbase
real,dimension(:,:),allocatable :: dtau_dp,dtau_dT
real,dimension(:,:,:),allocatable :: polytau

! read general input
call get_command_argument(1,inputdatei)
call read_invinput('inp_fast',trim(adjustl(inputdatei)))

inquire (file = 'inp_fast'//pathstr//'dtmess.inp',exist = dateidadec)
if (dateidadec) then
    iunit_dtmess = next_free_unit()
open (iunit_dtmess,file = 'inp_fast'//pathstr//'dtmess.inp',status = 'old',action = 'read')
    call gonext(iunit_dtmess,.false.)
    read (iunit_dtmess,*) dtmess
else
    dtmess = 0.0
end if


! check sizes of stored arrays and allocate arrays (and float constants)
call check_stored_file('wrk_fast'//pathstr//trim(abscodatei))

print *,'array sizes / imported integers: '
print *,''
print *, 'n_Tdisturb:       ',n_Tdisturb
print *, 'maxpoly:          ',maxpoly
print *, 'wvskal%ngrid_ref: ',wvskal%ngrid_ref
print *, 'n_tau:            ',n_tau
print *,''
print *,'other imported floats:'
print *,''
print *, 'altim_gnd_ref         ',altim_gnd_ref
print *, 'pPa_gnd_ref:          ',pPa_gnd_ref
print *, 'wvskal%firstnue_ref:  ',wvskal%firstnue_ref
print *, 'wvskal%dnuerel:       ',wvskal%dnuerel
print *,''

print *,'Allocating arrays...'
allocate (solspec_ref(wvskal%ngrid_ref),solspec(wvskal%ngrid_ref))
allocate (totcol_ref(n_tau))
allocate (dtau_dp(wvskal%ngrid_ref,n_tau),dtau_dT(wvskal%ngrid_ref,n_tau))
allocate (polytau(wvskal%ngrid_ref,maxpoly,n_tau))
allocate (wrktau(wvskal%ngrid_ref,n_tau),trm(wvskal%ngrid_ref))
print *,'...allocated!'

! read tabellated arrays
print *,'Reading tabellated arrays...'
call read_stored_arrays('wrk_fast'//pathstr//trim(abscodatei),solspec_ref,totcol_ref &
  ,polytau,dtau_dp,dtau_dT)
print *,'...done!'

! calculate tabellated wavenumber grid
do i = 1,wvskal%ngrid_ref
    wvskal%nue_ref(i) = wvskal%firstnue_ref * exp(real(i - 1,8) * wvskal%dnuerel)
end do
wvskal%lastnue_ref = wvskal%nue_ref(wvskal%ngrid_ref)

print *,'first tabellated wavenumber: ',wvskal%firstnue_ref
print *,'last tabellated wavenumber:  ',wvskal%lastnue_ref

! check compatibility of spectra, read observer position, JD, SZA
print *,'Checking spectra...'
call check_all_spectra()
print *,'...all spectra compatible!'
allocate (fullmesspec(wvskal%ngrid_mess))

! determine size for ILS arrays
! calculate radius of spectral self-apo boxcar (width on ref grid)
wvskal%isa = nint(0.70711 * 0.25 * semifov_ifm * semifov_ifm / wvskal%dnuerel)
sampdec = .false.
if (abs(wvskal%dnue_mess * 2.0d0 * instr%OPDmax - 1.0d0) .lt. 1.0d-4) then
    print *,'spectra minimally sampled!'
    sampdec = .true.
    wvskal%izf = 32
    ils_radius = n_ilsgrid_ms * wvskal%izf
    wvskal%dnue_ils = wvskal%dnue_mess / real(wvskal%izf,8)
end if
if (abs(wvskal%dnue_mess * 2.0d0 * instr%OPDmax - 0.8678143504d0) .lt. 1.0d-4) then
    print *,'spectra FFT sampled!'
    sampdec = .true.
    wvskal%izf = 37
    ils_radius = 1.15232 * real(n_ilsgrid_ms * wvskal%izf)
    wvskal%dnue_ils = wvskal%dnue_mess / real(wvskal%izf,8)
end if

if (.not. sampdec) then
    print *,wvskal%dnue_mess
    call warnout('Spectral grid not supported!',0)
end if

print *,'isa selfapo grid:    ',wvskal%isa
print *,'zerofill factor:     ',wvskal%izf
print *,'ILS dnue increment:  ',wvskal%dnue_ils
print *,'ILS radius:          ',ils_radius

allocate (ils(-ils_radius:ils_radius,n_job))

! init isa grid
wvskal%ngrid_isa = (wvskal%ngrid_ref - 1) / (2 * wvskal%isa) + 1
if (wvskal%ngrid_isa .gt. maxisagrid) then
    print *,wvskal%ngrid_isa
    print *,maxisagrid
    call warnout('Too many ngrid_isa points!',0)
end if
do i = 1,wvskal%ngrid_isa
    wvskal%nue_isa(i) = wvskal%firstnue_ref &
      * exp(real(i - 1,8) * wvskal%dnuerel * real(2 * wvskal%isa,8))
end do

print *, 'wvskal%ngrid_isa: ',wvskal%ngrid_isa

allocate (wrkisa(wvskal%ngrid_isa))

! determine spectral sections required for each job, fine to ref pointer
call init_mw_bounds()

! determine final set of ILS parameters (superimpose input file values with file header infos)
instr%apolin = obs(1)%mea_mess1 + (instr%apolin_inp - 1.0)
instr%apoeff = instr%apoeff_inp
instr%apophas = obs(1)%mep_mess1 + instr%apophas_inp
print *,'ILS apolin:  ',instr%apolin
print *,'ILS apoeff:  ',instr%apoeff
print *,'ILS phaserr: ',instr%apophas

! calculate ILS
do i = 1,n_job
    centernue = 0.5d0 * (job(i)%nuel_mess + job(i)%nuer_mess)
    call make_ils(centernue,ils(:,i))
end do

! write ILS to file
call tofile_ils('ils.dat',wvskal%dnue_ils,n_job,ils_radius,ils)

! read correction file for pT variations
if (pTdetaildec) call check_pTintraday(datumspfad,ndpTdt)
if (pTdetaildec) allocate (HHMMSSdpTdt(ndpTdt),dpdt(ndpTdt),dTdt(ndpTdt))
if (pTdetaildec) call read_pTintraday(datumspfad,ndpTdt,HHMMSSdpTdt,dpdt,dTdt)

! init append file for parameter output
call init_outparmfile('out_fast')

! init binary files for spectra output
do i = 1,n_job
    write (exta,'(I2.2)') i
    iunit_specout(i) = next_free_unit()    
    open (iunit_specout(i),file = 'out_fast'//pathstr//trim(sitename)//yymmddchar// &
      '-job'//exta//'.spc',access ='stream',status = 'replace',iostat = iowert)

    if (iowert .ne. 0) then
        print *,i
        call warnout ('init_specstofile: cannot open file!',0)
    end if
    write (iunit_specout(i)) n_spectra,job(i)%ngrid_mess
end do

print *,'performing retrievals...'
solspec = 0.0
ipTptr = 1
dpmean = 0.0
do i = 1,n_spectra

    ! read complete measured spectrum or spectra
    filename = trim(datumspfad)//pathstr//'cal'//pathstr//specname(i)
    call read_messpec(filename,wvskal%ngrid_mess1,fullmesspec(noff_chan1+1:noff_chan1+wvskal%ngrid_mess1)) ! read primary channel
    if (obs(i)%COchandec) then
        specname2 = specname(i)
        specname2(8:8) = 'M'
        filename = trim(datumspfad)//pathstr//'cal'//pathstr//specname2
        call read_messpec(filename,wvskal%ngrid_mess2,fullmesspec(1:wvskal%ngrid_mess2)) ! read CO channel
    end if
    ! Doppler scale of solar spectrum
    call sol_ephem(obs(i)%latrad,obs(i)%lonrad,obs(i)%JD,solskal)
    print *,'solar scale correction:',solskal
    call make_solspec(solskal,solspec_ref,solspec)
    ! call tofile_solspec('sol',wvskal%ngrid_ref,wvskal%nue_ref,solspec_ref,solspec)
    ! current pT correction
    if (pTdetaildec) then
        print *,'determining intraday dp,dT...'
        call give_dpTdt(specname(i),dtmess,ndpTdt,HHMMSSdpTdt,dpdt,dTdt,ipTptr,dp,dT)
        print *,'dp [mbar], dT [K]:',0.01 * dp,dT
        dpmean = dpmean + dp
    else
        dp = 0.0
        dT = 0.0
    end if

    ! take refraction into account if SEA in *.bin-file is unrefracted
    ! (refractdec = T - refracted SEA in file / refractdec = F - unrefracted SEA in file)
    if (.not. refractdec) then
        obs(i)%sza_rad = obs(i)%sza_rad &
          - refraction_rad(obs(i)%sza_rad,pPa_gnd_ref + dp,TKel_gnd_ref + dT)
    end if

    ! work through fit jobs
    do j = 1,n_job

        if (job(j)%nuel_mess .gt. nuechandiv .or. obs(i)%COchandec) then

            print *,'processing spectrum job: ',i,j
            ! prepare tau for selected species
            print *,'make_tau ...'
            if (ptdetaildec) then
                call make_tau_extd(i,j,polytau,dtau_dp,dtau_dT,dp,dT,wrktau)
            else
                call make_tau(i,j,polytau,wrktau)
            end if
            ! init column scaling factors, baseline parameters, spectral scaling parms
            if (i .eq. 1) then
                do k = 1,n_tau
                    if (job(j)%method(k) .eq. 2) then
                        job(j)%colskal(k) = 1.0
                        job(j)%colskal_persist(k) = 1.0
                    else
                        job(j)%colskal(k) = 0.0
                        job(j)%colskal_persist(k) = 0.0
                    end if
                end do
                job(j)%baseparm(1:job(j)%nbase) = 1.0
                job(j)%baseparm_persist(1:job(j)%nbase) = 1.0
                job(j)%epsnueskal = 0.0
                job(j)%epsnueskal_persist = 0.0
            else
               do k = 1,n_tau
                    if (job(j)%method(k) .eq. 2) then
                        job(j)%colskal(k) = job(j)%colskal_persist(k)
                    end if
                end do
                job(j)%baseparm(1:job(j)%nbase) = job(j)%baseparm_persist(1:job(j)%nbase)
                job(j)%epsnueskal = job(j)%epsnueskal_persist
            end if

            ! determine factor between derivative and nueskal units
            nueskalfaktor = 2.0 * wvskal%dnue_mess / real(job(j)%nuel_mess + job(j)%nuer_mess)

            ! allocate arrays (measurement coarse grid, job specific number of gridpoints)
            print *,'allocating job-specific arrays ...'
            allocate (basexils(job(j)%ngrid_mess),specxils(job(j)%ngrid_mess) &
              ,messxils(job(j)%ngrid_mess),dspecxilsdnue(job(j)%ngrid_mess) &
              ,weightxils(job(j)%ngrid_mess))
            allocate (dspecxilsdcol(job(j)%ngrid_mess,n_tau) &
              ,dwrkxilsdbase(job(j)%ngrid_mess,job(j)%nbase) &
              ,dspecxilsdbase(job(j)%ngrid_mess,job(j)%nbase))

            ! prepare deweigting vector
            if (job(j)%ndww .gt. 0) then
                print *,'init deweighting vector...'
                call init_weights(j,weightxils)
            else
                weightxils = 1.0
            end if

            ! prepare matrices for inversion
            ! order of derivatives: gases, baseline parms, spectral scale
            nderi = job(j)%nderigas + job(j)%nbase + 1
            allocate (jak(job(j)%ngrid_mess,nderi),jtj(nderi,nderi),jtj_inv(nderi,nderi))
            allocate (dparm(nderi))

            ! prepare baseline derivatives
            specxils = 1.0
            call make_dspecdbase(j,dwrkxilsdbase)

            ! before iteration loop: calculate spectrum and derivatives for the first time
            ! (use first-guess values)
            call make_trans(j,wrktau,solspec,trm)
            ! call tofile_trm('trm',j,wvskal%ngrid_ref,job(j)%igridl_ref,job(j)%igridr_ref &
            !   ,wvskal%nue_ref,trm)
            call make_baseline(j,job(j)%baseparm(1:job(j)%nbase),basexils)
            call make_spec(j,trm,ils(:,j),wrkisa,specxils,dspecxilsdnue)

            ! call tofile_specxils('specxils',j,job(j)%ngrid_mess,job(j)%nuel_mess &
            !   ,wvskal%dnue_mess,specxils)

            call make_dspecdcol(j,wrktau,trm &
              ,ils(:,j),wrkisa,dspecxilsdcol)

            ! apply empirical background continuum on spectrum and nue + col derivatives
            do k = 1,job(j)%nbase
                do l = 1,job(j)%ngrid_mess
                    dspecxilsdbase(l,k) = dwrkxilsdbase(l,k) * specxils(l)
                end do
            end do
            sollnorm = 0.0
            do k = 1,job(j)%ngrid_mess
                sollnorm = sollnorm + specxils(k)
                specxils(k) = specxils(k) * basexils(k)
            end do
            sollnorm = sollnorm / real(job(j)%ngrid_mess)
            do k = 1,job(j)%ngrid_mess
                dspecxilsdnue(k) = dspecxilsdnue(k) * basexils(k)
            end do
            do k = 1,n_tau
                if (job(j)%method(k) .eq. 2) then
                    do l = 1,job(j)%ngrid_mess
                        dspecxilsdcol(l,k) = dspecxilsdcol(l,k) * basexils(l)
                    end do
                end if
            end do

            ! fill derivatives into Jacobean (sequence: column, baseline, shift)
            icount = 1
            do k = 1,n_tau
                if (job(j)%method(k) .eq. 2) then
                    jak(:,icount) = dspecxilsdcol(:,k)
                    icount = icount + 1
                end if
            end do
            do k = 1,job(j)%nbase
                jak(:,icount) = dspecxilsdbase(:,k)
                icount = icount + 1
            end do
            jak(:,icount) = dspecxilsdnue
            ! call tofile_jak('jak',j,job(j)%ngrid_mess,nderi,jak)

            ! cut and normalize measured spectrum
            call specnormcut(j,sollnorm,fullmesspec,messxils)
            ! call tofile_specxils('messxils',j,job(j)%ngrid_mess,job(j)%nuel_mess &
            !   ,wvskal%dnue_mess,messxils)
        
            ! iterated inversion
            iiter = 1
            damping = 1.0
            convergdec = .false.
            do while (.not. convergdec)

                if (iiter .gt. 5) damping = 0.5

                ! perform inversion
                call make_jtj(job(j)%ngrid_mess,nderi,weightxils,jak,jtj)
                call matinvers(nderi,0.0,jtj,jtj_inv,inverfolg)
                if (.not. inverfolg) then
                    LMstab = 1.0e-9 * largest_EVal(nderi,jtj)
                    do while (.not. inverfolg)
                        print *,'warning: inverted matrix incorrect!'
                        call matinvers(nderi,LMstab,jtj,jtj_inv,inverfolg)
                        LMstab = 3.0d0 * LMstab
                    end do
                end if
                call give_dparms(job(j)%ngrid_mess,nderi,jtj_inv,jak,messxils,specxils,dparm)

                ! update parameters (sequence: column, baseline, shift)
                icount = 1
                do k = 1,n_tau
                    if (job(j)%method(k) .eq. 2) then
                        job(j)%colskal(k) = job(j)%colskal(k) + damping * dparm(icount)
                        icount = icount + 1
                    end if
                end do
                do k = 1,job(j)%nbase
                    job(j)%baseparm(k) = job(j)%baseparm(k) + damping * dparm(icount)
                    icount = icount + 1
                end do
                job(j)%epsnueskal = job(j)%epsnueskal + damping * nueskalfaktor * dparm(icount)

                ! check convergence
                call check_converg(job(j)%ngrid_mess,nderi,jak,dparm,convergdec)
                job(j)%rms = give_rms(job(j)%ngrid_mess,weightxils,messxils,specxils)
                print *,'spectrum job iteration',i,j,iiter,job(j)%rms

                if (iiter .gt. 9) exit

                if (.not. convergdec) then

                    iiter = iiter + 1

                    ! calculate transmission and derivatives of transmission spectrum
                    call make_trans(j,wrktau,solspec,trm)
                    ! call tofile_trm('trm',j,wvskal%ngrid_ref,job(j)%igridl_ref,job(j)%igridr_ref &
                    !   ,wvskal%nue_ref,trm)
                    call make_baseline(j,job(j)%baseparm(1:job(j)%nbase),basexils)
                    call make_spec(j,trm,ils(:,j),wrkisa,specxils,dspecxilsdnue)
                    ! call tofile_specxils('specxils',j,job(j)%ngrid_mess,job(j)%nuel_mess &
                    !   ,wvskal%dnue_mess,specxils)

                    call make_dspecdcol(j,wrktau,trm,ils(:,j),wrkisa,dspecxilsdcol)

                    ! apply empirical background continuum on spectrum and nue + col derivatives
                    do k = 1,job(j)%nbase
                        do l = 1,job(j)%ngrid_mess
                            dspecxilsdbase(l,k) = dwrkxilsdbase(l,k) * specxils(l)
                        end do
                    end do
                    do k = 1,job(j)%ngrid_mess
                        specxils(k) = specxils(k) * basexils(k)
                    end do
                    do k = 1,job(j)%ngrid_mess
                        dspecxilsdnue(k) = dspecxilsdnue(k) * basexils(k)
                    end do
                    do k = 1,n_tau
                        if (job(j)%method(k) .eq. 2) then
                            do l = 1,job(j)%ngrid_mess
                                dspecxilsdcol(l,k) = dspecxilsdcol(l,k) * basexils(l)
                            end do
                        end if
                    end do

                    ! fill derivatives into Jacobean (sequence: column, baseline, shift)
                    icount = 1
                    do k = 1,n_tau
                        if (job(j)%method(k) .eq. 2) then
                            jak(:,icount) = dspecxilsdcol(:,k)
                            icount = icount + 1
                        end if
                    end do
                    do k = 1,job(j)%nbase
                        jak(:,icount) = dspecxilsdbase(:,k)
                        icount = icount + 1
                    end do
                    jak(:,icount) = dspecxilsdnue
                    ! call tofile_jak('jak',j,job(j)%ngrid_mess,nderi,jak)

                    ! spectral scaling and ordinate scaling of measured spectrum
                    !call shiftnormcut(j,sollnorm,sincils,fullmesspec,messxils)

                end if ! only done if convergdec = F
            
            end do ! inversion iteration

            job(j)%niter = iiter

            ! write measured and calculated job spectrum to file            
            write (iunit_specout(j)) specname(i)
            write (iunit_specout(j)) messxils(1:job(j)%ngrid_mess)
            write (iunit_specout(j)) specxils(1:job(j)%ngrid_mess)

            ! deallocate job specific coarse grid arrays
            deallocate (dparm)
            deallocate (jak,jtj,jtj_inv)
            deallocate (basexils,specxils,messxils,dspecxilsdnue,weightxils)
            deallocate (dspecxilsdcol,dwrkxilsdbase,dspecxilsdbase)

        else

            job(j)%niter = 0
            job(j)%rms = 0.0
            job(j)%colskal = 0.0
            job(j)%baseparm(1:job(j)%nbase) = 1.0
            job(j)%epsnueskal = 0.0

        end if

    end do ! j work through fit jobs

    ! postprocessing (apply AICF + ADCF on columns, calculate XAIR, XVMR)
    call postprocessing(dp,totcol_ref,i)

    ! append results
    call append_parms('out_fast',dp,dT,totcol_ref,i)

    ! update persistent parameters
    do j = 1,n_job
        if (job(j)%nuel_mess .gt. nuechandiv .or. obs(i)%COchandec) then
            if (job(j)%niter .lt. 10) then
                icount = 1
                do k = 1,n_tau
                    if (job(j)%method(k) .eq. 2) then
                        job(j)%colskal_persist(k) = &
                          persist * job(j)%colskal_persist(k) + (1.0 - persist) * job(j)%colskal(k)
                        icount = icount + 1
                    end if
                end do
                do k = 1,job(j)%nbase
                    job(j)%baseparm_persist(k) = &
                      persist * job(j)%baseparm_persist(k) + (1.0 - persist) * job(j)%baseparm(k)
                    icount = icount + 1
                end do
                job(j)%epsnueskal_persist = &
                  persist * job(j)%epsnueskal_persist + (1.0 - persist) * job(j)%epsnueskal
            end if ! niter < 10
        end if ! job applicable in spectral range covered by current measured spectrum
    end do
    
end do ! i work through spectra

dpmean = dpmean / real(n_spectra)
if (abs(0.01 * dpmean) .gt. 10.0) then
    print *,'dpmean [hPa]: ',0.01 * dpmean
    call warnout('Warning: dpmean exceeds 10 mbar!',1)
end if

print *,'Deallocating arrays ...'
deallocate (fullmesspec)
if (pTdetaildec) deallocate (HHMMSSdpTdt,dpdt,dTdt)
deallocate (wrkisa)
deallocate (ils)
deallocate (solspec_ref,solspec)
deallocate (wrktau,trm)
deallocate (totcol_ref)
deallocate (dtau_dp,dtau_dT)
deallocate (polytau)
print *,'...deallocated!'

do i = 1,n_job
    close (iunit_specout(i))
end do

print *,'Program invers10 finished!'

end program invers10











!====================================================================
!  append_parms
!====================================================================
subroutine append_parms(pfadname,dp,dT,totcol_ref,ispec)

use globinv10

implicit none

character(len=*),intent(in) :: pfadname
real,intent(in) :: dp,dT
real(8),dimension(n_tau),intent(in) :: totcol_ref
integer,intent(in) :: ispec

character(len=4000) :: zeile
integer :: iunit_inv,next_free_unit,iowert,i,j,ipos

write(zeile(1:13),'(F13.5)') obs(ispec)%JD
write(zeile(14:15),'(A)') '  '
write(zeile(16:27),'(A)') specname(ispec)
write(zeile(22:33),'(A)') specname(ispec)
write(zeile(22:27),'(A)') '      '
write(zeile(30:33),'(A)') '    '
write(zeile(32:39),'(1X,F7.2)') 0.01 * (pPa_gnd_ref + dp)
write(zeile(40:47),'(1X,F7.2)') dT + TKel_gnd_ref
write(zeile(48:55),'(1X,F7.3)') radtograd * obs(ispec)%latrad
write(zeile(56:64),'(1X,F8.3)') radtograd * obs(ispec)%lonrad
write(zeile(65:71),'(1X,F6.1)') obs(ispec)%altim
write(zeile(72:79),'(1X,F7.2)') radtograd * obs(ispec)%sza_rad
write(zeile(80:87),'(1X,F7.2)') obs(ispec)%azimuth_deg

ipos = 88

! XVMRs
do i = 1,n_job
    do j = 1,n_tau
        if (job(i)%method(j) .eq. 2) then
            write(zeile(ipos:ipos+13),'(2X,ES12.5)') postpro(i)%XVMR(j)
            ipos = ipos + 14
        end if
    end do
end do

do i = 1,n_job
    write(zeile(ipos:ipos+13),'(2X,I12)') job(i)%niter
    ipos = ipos + 14
    write(zeile(ipos:ipos+13),'(2X,ES12.5)') job(i)%rms
    ipos = ipos + 14
    do j = 1,n_tau
        if (job(i)%method(j) .eq. 2) then
            write(zeile(ipos:ipos+13),'(2X,ES12.5)') job(i)%colskal(j)
            ipos = ipos + 14
            write(zeile(ipos:ipos+13),'(2X,ES12.5)') job(i)%colskal(j) * totcol_ref(j)
            ipos = ipos + 14
        end if
    end do
    do j = 1,job(i)%nbase
        write(zeile(ipos:ipos+13),'(2X,ES12.5)') job(i)%baseparm(j)
        ipos = ipos + 14
    end do
    write(zeile(ipos:ipos+13),'(2X,ES12.5)') job(i)%epsnueskal
    ipos = ipos + 14
end do

iunit_inv = next_free_unit()
open (iunit_inv,file = pfadname//pathstr//trim(sitename)//yymmddchar//'-invparms.dat'&
  ,status = 'old',iostat = iowert,position = 'append',action = 'write')
if (iowert .ne. 0) then
    call warnout ('append_parms: cannot open file!',0)
end if
write (iunit_inv,'(A)') zeile(1:ipos-1)

close (iunit_inv)

end subroutine append_parms



!====================================================================
!  check_all_spectra: performs check_spectrum for all spectra
!====================================================================
subroutine check_all_spectra

use globinv10

implicit none

character(len=12) :: specname2
logical :: specdadec
integer :: i,irefCO
real(8) :: latrad,lonrad,altim,JD,sza_rad,azimuth_deg,opdmax

! read entries from all CO channels (if available)
anyCOdec = .false.
do i = 1,n_spectra
    specname2 = specname(i)
    specname2(8:8) = 'M'
    call check_spectrum(datumspfad,specname2,obs(i)%COchandec,obs(i)%latrad,obs(i)%lonrad &
      ,obs(i)%altim,obs(i)%JD,obs(i)%sza_rad,obs(i)%azimuth_deg,obs(i)%mpd2,obs(i)%mea_mess2 &
      ,obs(i)%mep_mess2,obs(i)%firstnue_mess2,obs(i)%dnue_mess2,obs(i)%ngrid_mess2)
    if (obs(i)%COchandec .and. .not. anyCOdec) then
        anyCOdec = .true.
        irefCO = i
    end if
end do

if (anyCOdec) then
    print *,'CO spectra detected!'
end if

! read entries from all primary channels (check consistency coords, JD, sza_rad wrt CO channel)
do i = 1,n_spectra
    if (obs(i)%COchandec) then
        latrad = obs(i)%latrad
        lonrad = obs(i)%lonrad
        altim = obs(i)%altim
        JD = obs(i)%JD
        sza_rad = obs(i)%sza_rad
        azimuth_deg = obs(i)%azimuth_deg
    end if
    call check_spectrum(datumspfad,specname(i),specdadec,obs(i)%latrad,obs(i)%lonrad &
      ,obs(i)%altim,obs(i)%JD,obs(i)%sza_rad,obs(i)%azimuth_deg,obs(i)%mpd1,obs(i)%mea_mess1 &
      ,obs(i)%mep_mess1,obs(i)%firstnue_mess1,obs(i)%dnue_mess1,obs(i)%ngrid_mess1)
    if (.not. specdadec) then
        print *,specname(i)
        call warnout('listed spectrum inaccessible!',0)
    end if
    if (obs(i)%COchandec) then
        if (abs(obs(i)%latrad - latrad) + abs(obs(i)%lonrad - lonrad) .gt. 1.0d-5) then
            print *,specname(i)
            call warnout('incompatible coords!',0)
        end if
        if (abs(obs(i)%altim - altim) .gt. 1.0d-1) then
            print *,specname(i)
            call warnout('incompatible altitudes!',0)
        end if
        if (abs(obs(i)%JD - JD) .gt. 1.0d-5) then
            print *,specname(i)
            call warnout('incompatible JD!',0)
        end if
        if (abs(obs(i)%sza_rad - sza_rad) .gt. 1.0d-4) then
            print *,specname(i)
            call warnout('incompatible SZA!',0)
        end if
        if (abs(cos(gradtorad * obs(i)%azimuth_deg) - cos(gradtorad * azimuth_deg)) .gt. 1.0d-3) then
            print *,specname(i)
            call warnout('incompatible azimuth!',0)
        end if
        if (abs(obs(i)%mea_mess1 - obs(i)%mea_mess2) .gt. 1.0d-6) then
            print *,specname(i)
            call warnout('apolin differs between channels!',0)
        end if
        if (abs(obs(i)%mep_mess1 - obs(i)%mep_mess2) .gt. 1.0d-6) then
            print *,specname(i)
            call warnout('apophas differs between channels!',0)
        end if
    end if
end do

! Check that firstnue,dnue_mess,ngrid_mess are identical for all prim chan spectra
do i = 2,n_spectra
    if (abs(obs(i)%firstnue_mess1 - obs(1)%firstnue_mess1) .gt. 1.0d-4) then
        print *,specname(i)
        call warnout('firstnue_mess1 deviates!',0)
    end if
    if (abs(obs(i)%dnue_mess1 / obs(1)%dnue_mess1 - 1.0d0) .gt. 1.0d-6) then
        print *,specname(i)
        call warnout('dnue_mess1 deviates!',0)
    end if
    if (obs(i)%ngrid_mess1 - obs(1)%ngrid_mess1 .ne. 0) then
        print *,specname(i)
        call warnout('ngrid_mess1 deviates!',0)
    end if
    if (abs(obs(i)%mea_mess1 - obs(1)%mea_mess1) .gt. 1.0d-6) then
        print *,specname(i)
        call warnout('apolin not constant!',0)
    end if
    if (abs(obs(i)%mep_mess1 - obs(1)%mep_mess1) .gt. 1.0d-6) then
        print *,specname(i)
        call warnout('apophas not constant!',0)
    end if

end do

! Check that obs%mpd agrees wit EM27/SUN OPDmax as set in input file
do i = 1,n_spectra
    if (abs(obs(i)%mpd1 - instr%opdmax) .gt. 0.0001) then
        print *,specname(i)
        call warnout('inconsistent obs%mpd!',0)
    end if
    if (obs(i)%COchandec) then
        if (abs(obs(i)%mpd2 - instr%opdmax) .gt. 0.0001) then
            print *,specname(i)
            call warnout('inconsistent obs%mpd!',0)
        end if
    end if
end do

! Check that firstnue,dnue_mess,ngrid_mess are identical for all CO chan spectra
! Check that dnue_mess1 and dnue_mess1 agree
do i = 1,n_spectra
    if (obs(i)%COchandec) then
        if (abs(obs(i)%dnue_mess2 / obs(1)%dnue_mess1 - 1.0d0) .gt. 1.0d-6) then
            print *,specname(i)
            call warnout('dnue_mess2 dnue_mess1 differ!',0)
        end if
        if (obs(i)%ngrid_mess2 - obs(irefCO)%ngrid_mess2 .ne. 0) then
            print *,specname(i)
            call warnout('ngrid_mess2 deviates!',0)
        end if
    end if
end do

! determine final choice for dnue_mess, firstnue_mess, lastnue_mess
! (will be used for construction of array with measured spectral fluxes)
wvskal%dnue_mess = obs(1)%dnue_mess1
if (anyCOdec) then
    wvskal%firstnue_mess = obs(irefCO)%firstnue_mess2
    noff_chan1 = nint((obs(1)%firstnue_mess1 - obs(irefCO)%firstnue_mess2) / wvskal%dnue_mess)
    if (noff_chan1 .lt. 0) then
        print *,noff_chan1
        call warnout('Negative noff_chan1!',0)
    end if
    if ((obs(irefCO)%ngrid_mess2 - noff_chan1) .gt. obs(1)%ngrid_mess1) then
        call warnout('Spectral cov chan1 < chan2',0)
    end if
    wvskal%ngrid_mess = noff_chan1 + obs(irefCO)%ngrid_mess1
    wvskal%ngrid_mess1 = obs(1)%ngrid_mess1
    wvskal%ngrid_mess2 = obs(irefCO)%ngrid_mess2
else
    wvskal%firstnue_mess = obs(1)%firstnue_mess1
    noff_chan1 = 0
    wvskal%ngrid_mess = obs(1)%ngrid_mess1
    wvskal%ngrid_mess1 = obs(1)%ngrid_mess1
    wvskal%ngrid_mess2 = 0
end if
wvskal%lastnue_mess = wvskal%firstnue_mess + wvskal%dnue_mess &
  * real(wvskal%ngrid_mess - 1,8)

print *,'firstnue_mess: ',wvskal%firstnue_mess
print *,'lastnue_mess:  ',wvskal%lastnue_mess
print *,'dnue_mess:     ',wvskal%dnue_mess
print *,'ngrid_mess:    ',wvskal%ngrid_mess
print *,'ngrid_mess1:   ',wvskal%ngrid_mess1
print *,'ngrid_mess2:   ',wvskal%ngrid_mess2

end subroutine check_all_spectra



!====================================================================
!  check_convergdec
!====================================================================
subroutine check_converg(ngrid,nderi,jak,dparm,convergdec)

implicit none

integer,intent(in) :: ngrid,nderi
real,dimension(ngrid,nderi),intent(in) :: jak
real,dimension(nderi),intent(in) :: dparm
logical,intent(out) :: convergdec

integer :: i,j
real :: maxwert,neuwert

maxwert = 0.0
do i = 1,nderi
    do j = 1,ngrid
        neuwert = abs(dparm(i) * jak(j,i))
        if (neuwert .gt. maxwert) maxwert = neuwert
    end do
end do

if (maxwert .gt. 0.0005) then
    convergdec = .false.
else
    convergdec = .true.
end if

end subroutine check_converg



!====================================================================
!  check_pTintraday
!====================================================================
subroutine check_pTintraday(datumspfad,ndpTdt)

use globinv10, only : pathstr

implicit none

character(len=*),intent(in) :: datumspfad
integer,intent(out) :: ndpTdt

character(len=300) :: zeile
logical :: marke
integer :: iunit_inv,next_free_unit,iowert

iunit_inv = next_free_unit()
open (iunit_inv,file = trim(datumspfad)//pathstr//'pT'//pathstr//'pT_intraday.inp'&
  ,iostat = iowert,status = 'old',action = 'read')

if (iowert .ne. 0) then
    call warnout ('Cannot read pT_intraday file!',0)
end if

call gonext(iunit_inv,.false.)
marke = .false.
ndpTdt = 0
do while (.not. marke)
    read(iunit_inv,'(A)') zeile    
    if (zeile(1:3) .eq. '***') then
        marke = .true.
    else
        ndpTdt = ndpTdt + 1
    end if
end do
close (iunit_inv)

print *,'number of data lines in pT intraday file: ',ndpTdt

end subroutine check_pTintraday



!====================================================================
!  check_spectrum: checks wavenumber bounds of spectrum
!====================================================================
subroutine check_spectrum(datumspfad,specname,specdadec,latrad,lonrad,altim &
  ,JD,sza_rad_app,azimuth_deg,opdmax,mea,mep,firstnue_mess,dnue_mess,ngrid_mess)

use globinv10,only : pathstr,gradtorad

implicit none

character(len=*),intent(in) :: datumspfad
character(len=12),intent(in) :: specname
logical,intent(out) :: specdadec
real(8),intent(out) :: latrad,lonrad,altim,JD,sza_rad_app,azimuth_deg,opdmax,mea,mep &
  ,firstnue_mess,dnue_mess
integer,intent(out) :: ngrid_mess

character(2) :: dumchar
character(len=20) :: ortchar
character(len=6) :: datchar
integer :: iunit_inv,next_free_unit,i,iowert,ilskind,nfilter
real(8) :: utzeith,appelev_deg,duration,latdeg,londeg,altikm,give_JD

iunit_inv = next_free_unit()
open (iunit_inv,file = trim(datumspfad)//pathstr//'cal'//pathstr//specname,iostat = iowert &
  ,status = 'old',action = 'read')

if (iowert .ne. 0) then
    !print *,trim(datumspfad)//pathstr//'cal'//pathstr//specname
    !call warnout ('Cannot open measured spectrum!',0)
    specdadec = .false.

    latrad = 999.99d0
    lonrad = 999.99d0
    altikm = 9999.99d0
    JD = 99999999.99d0
    sza_rad_app = 999.99d0
    mea = 999.99d0
    mep = 999.99d0
    firstnue_mess = 9999.9d0
    dnue_mess = 999.99d0
else
    specdadec = .true.

    call gonext(iunit_inv,.false.)
    read (iunit_inv,'(A)') ortchar
    read (iunit_inv,'(A)') datchar
    read (iunit_inv,*) utzeith
    read (iunit_inv,*) appelev_deg
    read (iunit_inv,*) azimuth_deg
    read (iunit_inv,*) duration
    read (iunit_inv,*) latdeg
    read (iunit_inv,*) londeg
    read (iunit_inv,*) altikm
    latrad = gradtorad * latdeg
    lonrad = gradtorad * londeg
    altim = 1000.0 * altikm

    call gonext(iunit_inv,.false.)
    read (iunit_inv,*) nfilter
    read (iunit_inv,*) opdmax

    call gonext(iunit_inv,.false.)
    read (iunit_inv,*) ilskind
    if (ilskind .ne. 1) then
        print *,specname
        print *,ilskind
        call warnout('ILS is not simple!',0)
    end if
    read (iunit_inv,*) mea,mep

    close (iunit_inv)

    JD = give_JD(datchar,utzeith)
    sza_rad_app = gradtorad * (90.0d0 - appelev_deg)

    iunit_inv = next_free_unit()
    open (iunit_inv,file = trim(datumspfad)//pathstr//'cal'//pathstr//specname &
      ,access ='stream',iostat = iowert,status = 'old',action = 'read')

    if (iowert .ne. 0) then
        print *,trim(datumspfad)//pathstr//'cal'//pathstr//specname
        call warnout ('Cannot open measured spectrum!',0)
    end if

    do i = 1,6
        call gonext(iunit_inv,.true.)
    end do
    read(iunit_inv) dumchar
    read(iunit_inv) firstnue_mess
    read(iunit_inv) dnue_mess
    read(iunit_inv) ngrid_mess

    close (iunit_inv)
end if

end subroutine check_spectrum



!====================================================================
!  check_stored_file: reads integers and floats in file header
!====================================================================
subroutine check_stored_file(filename)

use globinv10

implicit none

character(len=*),intent(in) :: filename

integer :: iunit_inv,next_free_unit,iowert

iunit_inv = next_free_unit()
open (iunit_inv,file = filename,access ='stream',iostat = iowert &
  ,status = 'old',action = 'read')

if (iowert .ne. 0) then
    print *,filename
    call warnout ('Cannot access tabellated x-sections!',0)
end if

! all integers for array allocations
read (iunit_inv) n_Tdisturb
read (iunit_inv) maxpoly
read (iunit_inv) wvskal%ngrid_ref
read (iunit_inv) n_tau

if (wvskal%ngrid_ref .gt. maxnuegrid) then
    print *,wvskal%ngrid_ref
    print *,maxnuegrid
    call warnout('Too many ngrid_ref points!',0)
end if

! all floats for further aux infos
read (iunit_inv) altim_gnd_ref
read (iunit_inv) pPa_gnd_ref
read (iunit_inv) TKel_gnd_ref
read (iunit_inv) wvskal%firstnue_ref
read (iunit_inv) wvskal%dnuerel

close (iunit_inv)

end subroutine check_stored_file



!====================================================================
!  give_dpdT: determine current dp,dT
!====================================================================
subroutine give_dpTdt(specname,dtmess,ndpTdt,HHMMSSdpTdt,dpdt,dTdt,ipTptr,dp,dT)

implicit none

character(len=12),intent(in) :: specname
real,intent(in) :: dtmess
integer,intent(in) :: ndpTdt
character(len=6),dimension(ndpTdt),intent(in) :: HHMMSSdpTdt
real,dimension(ndpTdt),intent(in) :: dpdt,dTdt
integer,intent(inout) :: ipTptr
real,intent(out) :: dp,dT

character(len=6) :: HHMMSSmess
real(8) :: abstand

HHMMSSmess = specname(1:6)

do while (dayfrac(HHMMSSmess,dtmess) .lt. dayfrac(HHMMSSdpTdt(ipTptr),0.0) .and. ipTptr .gt. 1)
    ipTptr = ipTptr - 1
end do
do while (dayfrac(HHMMSSmess,dtmess) .gt. dayfrac(HHMMSSdpTdt(ipTptr+1),0.0) .and. ipTptr .lt. ndpTdt - 2)
    ipTptr = ipTptr + 1
end do

abstand = (dayfrac(HHMMSSmess,dtmess) - dayfrac(HHMMSSdpTdt(ipTptr),0.0)) &
  / (dayfrac(HHMMSSdpTdt(ipTptr+1),0.0) - dayfrac(HHMMSSdpTdt(ipTptr),0.0))

if (abstand .gt. 1.0d0) abstand = 1.0d0
if (abstand .lt. 0.0d0) abstand = 0.0d0

! Note: dp is tabellated in hPa, whereas spectral derivative wrt p requires Pa
dp = 100.0 * ((1.0d0 - abstand) * dpdt(ipTptr) + abstand * dpdt(ipTptr+1))
dT = (1.0d0 - abstand) * dTdt(ipTptr) + abstand * dTdt(ipTptr+1)

contains

real function dayfrac(HHMMSS,dtmess)

character(len=6),intent(in) :: HHMMSS
real,intent(in) :: dtmess

integer :: inth,intmin,intsec

read (HHMMSS(1:2),fmt='(I2)') inth
read (HHMMSS(3:4),fmt='(I2)') intmin
read (HHMMSS(5:6),fmt='(I2)') intsec

dayfrac = (real(3600 * inth + 60 * intmin + intsec) + 3600.0 * dtmess) * 1.1574074e-5
if (dayfrac .lt. 0.0) dayfrac = dayfrac + 1.0
if (dayfrac .gt. 1.0) dayfrac = dayfrac - 1.0

end function dayfrac

end subroutine give_dpTdt



!====================================================================
!  give_dparms
!====================================================================
subroutine give_dparms(ngrid,nderi,jtj_inv,jak,messxils,specxils,dparm)

implicit none

integer,intent(in) :: ngrid,nderi
real,dimension(nderi,nderi),intent(in) :: jtj_inv
real,dimension(ngrid,nderi),intent(in) :: jak
real,dimension(ngrid),intent(in) :: messxils,specxils
real,dimension(nderi),intent(out) :: dparm

integer :: i,j,k
real(8) :: wrkdble

do i = 1,nderi
    wrkdble = 0.0d0
    do j = 1,nderi
        do k = 1,ngrid
            wrkdble = wrkdble + jtj_inv(j,i) * jak(k,j) * (messxils(k) - specxils(k))
        end do
    end do
    dparm(i) = wrkdble
end do

end subroutine give_dparms



!====================================================================
!  give_JD: calculate JD (Gregorian input dates)
!====================================================================
real(8) function give_JD(datchar,utzeith)

implicit none

character(len=6),intent(in) :: datchar 
real(8),intent(in) :: utzeith

integer :: werta,wertb,ijahr,imonat,itag
real(8) :: ftag

read(datchar(1:2),'(I2)') ijahr
read(datchar(3:4),'(I2)') imonat
read(datchar(5:6),'(I2)') itag

if (ijahr .gt. 70) then
    ijahr = ijahr + 1900
else
    ijahr = ijahr + 2000
end if

ftag = real(itag,8) + utzeith / 24.0d0

IF (imonat .eq. 1 .or. imonat .eq. 2) THEN
    ijahr = ijahr - 1
    imonat = imonat + 12
END IF

werta = int(0.01d0 * real(ijahr,8))
wertb = 2 - werta + int(0.25d0 * real(werta,8))

give_JD = real(int(365.25d0 * real(ijahr + 4716,8)),8) &
  + real(int(30.6001d0 * real(imonat + 1,8)),8) + ftag + real(wertb,8) - 1524.5d0

end function give_JD



!====================================================================
!  give_rms
!====================================================================
real function give_rms(ngrid,weight,messxils,specxils)

implicit none

integer,intent(in) :: ngrid
real,dimension(ngrid),intent(in) :: weight,messxils,specxils

integer :: i
real :: sumwert

sumwert = 0.0
do i = 1,ngrid
    sumwert = sumwert + weight(i) * weight(i) &
      * (messxils(i) - specxils(i)) * (messxils(i) - specxils(i))
end do
give_rms = sqrt(sumwert / real(ngrid))

end function give_rms



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
! init_mw_bounds: set wavenumber limits and grid bounds for each job
!====================================================================
subroutine init_mw_bounds()

use globinv10

implicit none

integer :: i,j
real(8) :: nue_extension

! determine wavenumber sections in measurement (adjust requested mw bounds)
do i = 1,n_job
    job(i)%nuel_mess = real(nint(job(i)%nuel_input / wvskal%dnue_mess),8) * wvskal%dnue_mess
    job(i)%nuer_mess = real(nint(job(i)%nuer_input / wvskal%dnue_mess),8) * wvskal%dnue_mess
    job(i)%igridl_mess = 1 + nint((job(i)%nuel_mess - wvskal%firstnue_mess) / wvskal%dnue_mess)
    job(i)%igridr_mess = 1 + nint((job(i)%nuer_mess - wvskal%firstnue_mess) / wvskal%dnue_mess)
    job(i)%ngrid_mess = job(i)%igridr_mess - job(i)%igridl_mess + 1
end do

do i = 1,n_job
    if (job(i)%nbase .gt. 3) then
        do j = 1,job(i)%nbase - 1 ! for each polynom
            job(i)%base_ptrr(j) = 1 + int((job(i)%ngrid_mess - 1) * j / (job(i)%nbase - 1))
        end do
        job(i)%base_ptrl(1) = 1
        do j = 2,job(i)%nbase - 1 ! for each polynom
            job(i)%base_ptrl(j) = job(i)%base_ptrr(j-1) + 1
        end do
    end if
end do

! determine required sections in tables (ref grid and isa grid)
nue_extension = wvskal%dnue_ils * real(ils_radius,8) + 5.0d0 / instr%OPDmax
do i = 1,n_job
    job(i)%igridl_isa = 1 + &
      log((job(i)%nuel_mess - nue_extension) / wvskal%firstnue_ref) &
        / (real(2 * wvskal%isa,8) * wvskal%dnuerel)
    job(i)%igridl_ref = 1 + (job(i)%igridl_isa - 1 - 3) * 2 * wvskal%isa
    job(i)%igridr_isa = 1 + &
      log((job(i)%nuer_mess + nue_extension) / wvskal%firstnue_ref) &
        / (real(2 * wvskal%isa,8) * wvskal%dnuerel)
    job(i)%igridr_ref = 1 + (job(i)%igridr_isa - 1 + 3) * 2 * wvskal%isa
    if (job(i)%igridl_isa .lt. 50 .or. job(i)%igridr_isa .gt. wvskal%ngrid_isa - 50) then
        print *,'Job:',i
        print *,'low extended bound:',job(i)%nuel_mess - nue_extension
        print *,'high extended bound:',job(i)%nuer_mess + nue_extension
        call warnout('outside spectral table!',0)
    end if
end do

!! determine required sections on equidistant fine grid (grid width as chosen in ILS table)
!nue_extension = wvskal%dnue_ils * real(ils_radius,8) + 4.0d0 / instr%OPDmax
!do i = 1,n_job
!    job(i)%nuel_fine = job(i)%nuel_mess - nue_extension
!    job(i)%nuer_fine = job(i)%nuer_mess + nue_extension
!    job(i)%igridl_fine = nint(job(i)%nuel_fine / wvskal%dnue_ils) + 1
!    job(i)%igridr_fine = nint(job(i)%nuer_fine / wvskal%dnue_ils) + 1
!end do

end subroutine init_mw_bounds



!====================================================================
! init_outparmfile
!====================================================================
subroutine init_outparmfile(pfadname)

use globinv10

implicit none

character(len=*),intent(in) :: pfadname

character(len=4000) :: headerchar
character(len=2) :: exta,extb
integer :: iunit_inv,next_free_unit,i,j,iowert,ipos

iunit_inv = next_free_unit()
open (iunit_inv,file = pfadname//pathstr//trim(sitename)//yymmddchar//'-invparms.dat'&
  ,iostat = iowert,status = 'replace',action = 'write')

if (iowert .ne. 0) then
    print *,'Cannot create output file:    '
    print *,pfadname//pathstr//trim(sitename)//yymmddchar//'-invparms.dat'
end if

! create file header
headerchar(1:14) = 'JulianDate    '
headerchar(15:24) = ' HHMMSS_ID'
headerchar(25:31) = '   SX  '
headerchar(32:39) = '  gndP  '
headerchar(40:47) = '  gndT  '
headerchar(48:55) = '  latdeg'
headerchar(56:63) = '  londeg'
headerchar(64:71) = '  altim '
headerchar(72:79) = '  appSZA'
headerchar(80:87) = ' azimuth'
ipos = 88

! XVMRs
do i = 1,n_job
    do j = 1,n_tau
        if (job(i)%method(j) .eq. 2) then
            headerchar(ipos:ipos+2) = '   '
            ipos = ipos + 3
            headerchar(ipos:ipos+7) = postpro(i)%Xident(j)
            ipos = ipos + 8
            headerchar(ipos:ipos+2) = '   '
            ipos = ipos + 3
        end if
    end do
end do

do i = 1,n_job
    write (exta,'(I2.2)') i

    headerchar(ipos:ipos+5) = '   job'
    ipos = ipos + 6
    headerchar(ipos:ipos+1) = exta
    ipos = ipos + 2
    headerchar(ipos:ipos+5) = '_niter'
    ipos = ipos + 6

    headerchar(ipos:ipos+5) = '   job'
    ipos = ipos + 6
    headerchar(ipos:ipos+1) = exta
    ipos = ipos + 2
    headerchar(ipos:ipos+5) = '_rms  '
    ipos = ipos + 6

    do j = 1,n_tau
        if (job(i)%method(j) .eq. 2) then
            write (extb,'(I2.2)') j
            headerchar(ipos:ipos+5) = '   job'
            ipos = ipos + 6
            headerchar(ipos:ipos+1) = exta
            ipos = ipos + 2
            headerchar(ipos:ipos+3) = '_gsf'
            ipos = ipos + 4
            headerchar(ipos:ipos+1) = extb
            ipos = ipos + 2
            write (extb,'(I2.2)') j
            headerchar(ipos:ipos+5) = '   job'
            ipos = ipos + 6
            headerchar(ipos:ipos+1) = exta
            ipos = ipos + 2
            headerchar(ipos:ipos+3) = '_gas'
            ipos = ipos + 4
            headerchar(ipos:ipos+1) = extb
            ipos = ipos + 2
        end if
    end do

    do j = 1,job(i)%nbase
        write (extb,'(I2.2)') j
        headerchar(ipos:ipos+5) = '   job'
        ipos = ipos + 6
        headerchar(ipos:ipos+1) = exta
        ipos = ipos + 2
        headerchar(ipos:ipos+3) = '_bsl'
        ipos = ipos + 4
        headerchar(ipos:ipos+1) = extb
        ipos = ipos + 2
    end do

    headerchar(ipos:ipos+5) = '   job'
    ipos = ipos + 6
    headerchar(ipos:ipos+1) = exta
    ipos = ipos + 2
    headerchar(ipos:ipos+5) = '_scl  '
    ipos = ipos + 6
end do

write (iunit_inv,'(A)') headerchar(1:ipos-1)

close (iunit_inv)

end subroutine init_outparmfile



!====================================================================
! Initialisierung der Gewichte fuer spektrale Stuetzstellen
!====================================================================
subroutine init_weights(ijob,weight)

use globinv10

implicit none

integer,intent(in) :: ijob
real,dimension(job(ijob)%ngrid_mess),intent(out) :: weight

integer :: i,idww
real(8) :: nue,wert,steep

weight = 1.0

do idww = 1,job(ijob)%ndww
    do i = 1,job(ijob)%ngrid_mess
        nue = job(ijob)%nuel_mess + wvskal%dnue_mess * real(i - 1,8)
        steep = 1.0d0 / (abs(job(ijob)%vw_steep(idww)) + 1.0d-3)
        wert =  1.0d0 / &
          (myweight(steep * (nue - real(job(ijob)%vw_bnds(idww),8))) + 1.0d0) &
          + 1.0d0 / (myweight(steep * (aimag(job(ijob)%vw_bnds(idww)) - nue)) + 1.0d0)
        weight(i) = weight(i) * wert
    end do
end do

contains

real(8) function myweight(xwert)

implicit none

real(8),intent(in) :: xwert

if (xwert .gt. 0.0d0) then
    myweight = 1.0d0 + xwert * (1.0d0 + xwert * (0.5d0 + xwert * xwert * xwert * 0.15d0))
else
    myweight = 1.0d0 / (1.0d0 + abs(xwert) * (1.0d0 + abs(xwert) &
      * (0.5d0 + abs(xwert) * abs(xwert) * abs(xwert) * 0.15d0)))
end if

end function myweight

end subroutine init_weights



!====================================================================
!  largest largest eigenvalue of matrix
!====================================================================
real function largest_EVal(nmax,matein)

implicit none

integer,intent(in) :: nmax
real,dimension(nmax,nmax),intent(in) :: matein

integer :: i,j,imax,icycle
real(8) :: wert,maxwert,norm
real(8),dimension(:),allocatable :: EV,EVnew

! find largest vector
maxwert = 0.0d0
do i = 1,nmax
    wert = 0.0
    do j = 1,nmax
        wert = wert + matein(j,i) * matein(j,i)
    end do
    if (wert .gt. maxwert) then
        wert = maxwert
        imax = i
    end if
end do

! Align vector to largest EV and find EW
allocate (EV(nmax),EVnew(nmax))
EV = 0.0d0
EV(imax) = 1.0d0
do icycle = 1,20
    EVnew = matmul(matein,EV)
    norm = dot_product(EV,EV)
    EV = EVnew / sqrt(norm)
end do

EVnew = matmul(matein,EV)
largest_EVal = sqrt(dot_product(EVnew,EVnew))

deallocate (EV,EVnew)

end function largest_EVal




!====================================================================
!  make_baseline
!====================================================================
subroutine make_baseline(ijob,baseparm,basexils)

use globinv10

implicit none

integer,intent(in) :: ijob
real,dimension(job(ijob)%nbase),intent(in) :: baseparm
real,dimension(job(ijob)%ngrid_mess),intent(out) :: basexils

integer :: i,j
real :: kwert,xwert,xr,c1,c2,c3

if (job(ijob)%nbase .eq. 1) then ! constant background value
    basexils = baseparm(1)
else
    if (job(ijob)%nbase .eq. 2) then ! linear (x range 0 ... 1)
        kwert = 1.0 / real(job(ijob)%ngrid_mess - 1)
        do i = 1,job(ijob)%ngrid_mess
            xwert = real(i - 1) * kwert
            basexils(i) = (1.0 - xwert) * baseparm(1) + xwert * baseparm(2)
        end do
    else
        if (job(ijob)%nbase .eq. 3) then ! quadratic (x range 0 ... 2)
            kwert = 2.0 / real(job(ijob)%ngrid_mess - 1)
            c1 = -1.5 * baseparm(1) + 2.0 * baseparm(2) - 0.5 * baseparm(3)
            c2 = 0.5 * baseparm(1) - baseparm(2) + 0.5 * baseparm(3)
            do i = 1,job(ijob)%ngrid_mess
                xwert = real(i - 1) * kwert
                basexils(i) = baseparm(1) + xwert * (c1 + xwert * c2)
            end do
        else
            ! general (x range 0 ... nbase - 1)
            kwert = real(job(ijob)%nbase - 1) / real(job(ijob)%ngrid_mess - 1)
            ! left parabola
            c1 = -1.5 * baseparm(1) + 2.0 * baseparm(2) - 0.5 * baseparm(3)
            c2 = 0.5 * baseparm(1) - baseparm(2) + 0.5 * baseparm(3)
            do i = job(ijob)%base_ptrl(1),job(ijob)%base_ptrr(1)
                xwert = real(i - 1) * kwert
                xr = xwert
                basexils(i) = baseparm(1) + xr * (c1 + xr * c2)                
            end do
            ! cubic
            do i = 2,job(ijob)%nbase - 2
                c1 = 0.5 * (baseparm(i+1) - baseparm(i-1))
                c2 = baseparm(i-1) - 2.5 * baseparm(i) + 2.0 * baseparm(i+1) - 0.5 * baseparm(i+2)
                c3 = -0.5 * baseparm(i-1) + 1.5 * baseparm(i) - 1.5 * baseparm(i+1) + 0.5 * baseparm(i+2)
                do j = job(ijob)%base_ptrl(i),job(ijob)%base_ptrr(i)
                    xwert = real(j - 1) * kwert
                    xr = xwert - real(i - 1)
                    basexils(j) = baseparm(i) + xr * (c1 + xr * (c2 + xr * c3))
                end do
            end do
            ! right parabola
            c1 = 0.5 * (baseparm(job(ijob)%nbase) - baseparm(job(ijob)%nbase-2))
            c2 = 0.5 * baseparm(job(ijob)%nbase-2) - baseparm(job(ijob)%nbase-1) &
              + 0.5 * baseparm(job(ijob)%nbase)
            do i = job(ijob)%base_ptrl(job(ijob)%nbase - 1),job(ijob)%base_ptrr(job(ijob)%nbase - 1)
                xwert = real(i - 1) * kwert
                xr = xwert - real(job(ijob)%nbase - 2)
                basexils(i) = baseparm(job(ijob)%nbase-1) + xr * (c1 + xr * c2)
            end do            
        end if
    end if
end if

end subroutine make_baseline



!====================================================================
!  make_dspecdbase
!====================================================================
subroutine make_dspecdbase(ijob,dwrkxilsdbase)

use globinv10

implicit none

integer,intent(in) :: ijob
real,dimension(job(ijob)%ngrid_mess,job(ijob)%nbase),intent(out) :: dwrkxilsdbase

integer :: i
real,dimension(job(ijob)%nbase) :: baseparm

baseparm(:) = 0.0
do i = 1,job(ijob)%nbase    
    baseparm(i) = 1.0
    call make_baseline(ijob,baseparm,dwrkxilsdbase(:,i))
    baseparm(i) = 0.0
end do

end subroutine make_dspecdbase



!====================================================================
!  make_dspecdcol
!====================================================================
subroutine make_dspecdcol(ijob,tau,trm,jobils,wrkisa,dspecxilsdcol)

use globinv10

integer,intent(in) :: ijob
real,dimension(wvskal%ngrid_ref,n_tau),intent(in) :: tau
real,dimension(wvskal%ngrid_ref),intent(in) :: trm
real,dimension(-ils_radius:ils_radius),intent(in) :: jobils
real,dimension(wvskal%ngrid_isa),intent(out) :: wrkisa
real,dimension(job(ijob)%ngrid_mess,n_tau),intent(out) :: dspecxilsdcol

integer :: itau,i,j,ioffset_ref,jlow,jhigh,iils
real :: rest
real(8) :: actnue,nue_ils_radius,sumwert,sumils,ilswert,xils,inv_dnue_ils
real,dimension(-2*wvskal%isa+1:2*wvskal%isa-1) :: isakernel

! prepare self-apo kernel
sumwert = 0.0d0
do i = -2 * wvskal%isa + 1,2 * wvskal%isa - 1
    isakernel(i) = 1.0 - abs(real(i)) / real(2 * wvskal%isa)
    sumwert = sumwert + isakernel(i)
end do
isakernel = isakernel / sumwert

do itau = 1,n_tau
    if (job(ijob)%method(itau) .eq. 2) then

        do i = job(ijob)%igridl_isa,job(ijob)%igridr_isa
            ioffset_ref = 2 * wvskal%isa * (i - 1) + 1
            sumwert = 0.0d0
            do j = -2 * wvskal%isa + 1,2 * wvskal%isa - 1
                sumwert = sumwert &
                  - tau(ioffset_ref+j,itau) * trm(ioffset_ref+j) * isakernel(j)
            end do
            wrkisa(i) = sumwert
        end do

        ! convolution
        nue_ils_radius = real(ils_radius,8) * wvskal%dnue_ils
        inv_dnue_ils = 1.0d0 / wvskal%dnue_ils
        do i = 1,job(ijob)%ngrid_mess
            actnue = (1.0d0 - job(ijob)%epsnueskal) &
              * (job(ijob)%nuel_mess + real(i - 1,8) * wvskal%dnue_mess)
            jlow = 1 + nint(log((actnue - nue_ils_radius) / wvskal%firstnue_ref) &
              / (real(2 * wvskal%isa,8) * wvskal%dnuerel))
            jhigh = 1 + nint(log((actnue + nue_ils_radius) / wvskal%firstnue_ref) &
              / (real(2 * wvskal%isa,8) * wvskal%dnuerel))
            sumwert = 0.0d0
            sumils = 0.0d0
            do j = jlow + 2,jhigh - 2
                xils = (actnue - wvskal%nue_isa(j)) * inv_dnue_ils
                iils = nint(xils)
                rest = xils - real(iils,8)
                ilswert = jobils(iils) + 0.5 * rest * (jobils(iils+1) - jobils(iils-1) &
                  + rest * (jobils(iils+1) - 2.0 * jobils(iils) + jobils(iils-1)))
                sumwert = sumwert + ilswert * wrkisa(j) &
                  * (wvskal%nue_isa(j+1) - wvskal%nue_isa(j-1))
                sumils = sumils + ilswert * (wvskal%nue_isa(j+1) - wvskal%nue_isa(j-1))
            end do
            dspecxilsdcol(i,itau) = sumwert / sumils
        end do
    else
        dspecxilsdcol(:,itau) = 0.0
    end if
end do

end subroutine make_dspecdcol



!====================================================================
!  subroutine make_ils: calculate entries for ILS table
!====================================================================
subroutine make_ils(actnue,ils)

use globinv10

implicit none

real(8),intent(in) :: actnue
real,dimension(-ils_radius:ils_radius),intent(inout) :: ils

integer :: i,j
real :: cosapo
real(8) :: sinuy,sinly,cosuy,cosly,term,modNBM,modlin,modquad,kwdeltaopd &
  ,deltay,sumwertg,sumwertu,sumwert,opdrel,term1g,term1u,term2g,term2u,align_skale
real(8),dimension(n_ifg) :: opd
real(8),dimension(2,n_ifg-1) :: awert,bwert
real(8),dimension(2,n_ifg) :: modulat

! scaling of misalignment parameters to current wavenumber (reference 7200 cm-1)
align_skale = (actnue / 7200.0d0)

! calculate modulation
do i = 1,n_ifg
    opdrel = real(i - 1,8) / real(n_ifg - 1,8)
    opd(i) = opdrel * instr%OPDmax + 1.0d-6
    ! self-apo, NBM apodisation
    term = (1.0d0 - opdrel * opdrel)
    modNBM = 0.152442d0 - 0.136176d0 * term + 0.983734d0 * term * term
    ! linear modulation loss
    modlin = (1.0 + align_skale * (instr%apolin - 1.0) * opdrel)
    ! quadratic modulation loss
    modquad = (1.0 + align_skale * align_skale * instr%apoeff * opdrel * opdrel)
    ! self apo
    !boxnue = 0.5d0 * instr%semiFOVint * instr%semiFOVint * actnue
    !term = pi * boxnue * opd(i)
    !modself = sin(term) / term
    modulat(1,i) = modNBM * modlin * modquad !* modself
    modulat(2,i) = modulat(1,i) * tan(align_skale * instr%apophas)
end do

! calculate ILS
do i = 1,n_ifg - 1 
    kwdeltaopd = 1.0d0 / (opd(i+1) - opd(i))
    awert(1,i) = (modulat(1,i) * opd(i+1) - modulat(1,i+1) * opd(i)) * kwdeltaopd
    bwert(1,i) = (modulat(1,i+1) - modulat(1,i)) * kwdeltaopd
    awert(2,i) = (modulat(2,i) * opd(i+1) - modulat(2,i+1) * opd(i)) * kwdeltaopd
    bwert(2,i) = (modulat(2,i+1) - modulat(2,i)) * kwdeltaopd
end do
do i = 0,ils_radius
    deltay = 2.0d0 * pi * (wvskal%dnue_ils * real(i,8) + 1.0d-6)
    sumwertg = 0.0d0
    sumwertu = 0.0d0
    do j = 1,n_ifg - 1
        sinuy = sin(opd(j+1) * deltay)
        sinly = sin(opd(j) * deltay)
        cosuy = cos(opd(j+1) * deltay)
        cosly = cos(opd(j) * deltay)
        term1g = awert(1,j) * (sinuy - sinly) / deltay
        term2g = bwert(1,j) * (cosuy + opd(j+1) * deltay * sinuy &
          - cosly - opd(j) * deltay * sinly) / (deltay * deltay)
        term1u = - awert(2,j) * (cosuy - cosly) / deltay
        term2u = - bwert(2,j) * (opd(j+1) * deltay * cosuy - sinuy &
          - opd(j) * deltay * cosly + sinly) / (deltay * deltay)
        sumwertg = sumwertg + term1g + term2g
        sumwertu = sumwertu + term1u + term2u
    end do
    ils(-i) = sqrt(2.0d0 * kwpi) * (sumwertg - sumwertu)
    ils(i) = sqrt(2.0d0 * kwpi) * (sumwertg + sumwertu)
end do

! damp ILS towards rim
do i = 1,ils_radius
    cosapo = cos(0.5 * pi * real(i * i,8) / real(ils_radius * ils_radius,8))
    ils(-i) = ils(-i) * cosapo
    ils(i) = ils(i) * cosapo
end do

! normalize
sumwert = 0.0d0
do i = -ils_radius,ils_radius
    sumwert = sumwert + ils(i)
end do
ils = ils / sumwert

end subroutine make_ils



!====================================================================
!  make_jtj
!====================================================================
subroutine make_jtj(ngrid,nderi,weight,jak,jtj)

implicit none

integer,intent(in) :: ngrid,nderi
real,dimension(ngrid),intent(in) :: weight
real,dimension(ngrid,nderi),intent(in) :: jak
real,dimension(nderi,nderi),intent(out) :: jtj

integer :: i,j,k
real(8) :: wert

do i = 1,nderi
    do j = i,nderi
        wert = 0.0d0
        do k = 1,ngrid
            wert = wert + jak(k,i) * weight(k) * jak(k,j)
        end do
        jtj(i,j) = wert
        jtj(j,i) = wert
    end do
end do

end subroutine make_jtj



!====================================================================
!  make_solspec
!====================================================================
subroutine make_solspec(solskalephem,solspec_ref,solspec)

use globinv10

implicit none

real(8),intent(in) :: solskalephem
real,dimension(wvskal%ngrid_ref),intent(in) :: solspec_ref
real,dimension(wvskal%ngrid_ref),intent(inout) :: solspec

integer :: i,j,ishift
real(8) :: verschiebung,rest

! shift in units of tabellated grid distance (wavenumber independent!)
verschiebung =  - solskalephem / wvskal%dnuerel
ishift = int(verschiebung)
rest = verschiebung - real(ishift,8)

do i = 1,n_job
    do j = job(i)%igridl_ref,job(i)%igridr_ref
        solspec(j) = (1.0 - rest) * solspec_ref(j+ishift) + rest * solspec_ref(j+ishift+1) 
    end do
end do

end subroutine make_solspec



!====================================================================
!  make_spec
!====================================================================
subroutine make_spec(ijob,trm,jobils,wrkisa,specxils,dspecxilsdnue)

use globinv10

implicit none

integer,intent(in) :: ijob
real,dimension(wvskal%ngrid_ref),intent(in) :: trm
real,dimension(-ils_radius:ils_radius),intent(in) :: jobils
real,dimension(wvskal%ngrid_isa),intent(out) :: wrkisa
real,dimension(job(ijob)%ngrid_mess),intent(out) :: specxils
real,dimension(job(ijob)%ngrid_mess),intent(out) :: dspecxilsdnue

integer :: i,j,ioffset_ref,jlow,jhigh,iils
real :: nue,kwmidnue,rest
real(8) :: actnue,nue_ils_radius,sumwert,ilswert,sumils,xils,inv_dnue_ils
real,dimension (-2*wvskal%isa+1:2*wvskal%isa-1) :: isakernel

! smoothing of trm (self apo)
sumwert = 0.0d0
do i = -2 * wvskal%isa + 1,2 * wvskal%isa - 1
    isakernel(i) = 1.0d0 + cos(pi * real(i,8) / real(2 * wvskal%isa,8))
    sumwert = sumwert + isakernel(i)
end do
isakernel = isakernel / sumwert
do i = job(ijob)%igridl_isa,job(ijob)%igridr_isa
    ioffset_ref = 2 * wvskal%isa * (i - 1) + 1
    sumwert = 0.0d0
    do j = -2 * wvskal%isa + 1,2 * wvskal%isa - 1
        sumwert = sumwert + trm(ioffset_ref+j) * isakernel(j)
    end do
    wrkisa(i) = sumwert
end do

! convolution
nue_ils_radius = real(ils_radius,8) * wvskal%dnue_ils
inv_dnue_ils = 1.0d0 / wvskal%dnue_ils
if (job(ijob)%nuer_mess * abs(job(ijob)%epsnueskal) .gt. 0.5d0) then
    print *,'warning: shift too big!'
    job(ijob)%epsnueskal = 0.5d0 / job(ijob)%nuer_mess * sign(1.0,job(ijob)%epsnueskal)
end if
do i = 1,job(ijob)%ngrid_mess
    actnue = (1.0d0 - job(ijob)%epsnueskal) &
      * (job(ijob)%nuel_mess + real(i - 1,8) * wvskal%dnue_mess)
    jlow = 1 + nint(log((actnue - nue_ils_radius) / wvskal%firstnue_ref) &
      / (real(2 * wvskal%isa,8) * wvskal%dnuerel))
    jhigh = 1 + nint(log((actnue + nue_ils_radius) / wvskal%firstnue_ref) &
      / (real(2 * wvskal%isa,8) * wvskal%dnuerel))
    sumwert = 0.0d0
    sumils = 0.0d0
    do j = jlow + 2,jhigh - 2
        xils = (actnue - wvskal%nue_isa(j)) * inv_dnue_ils
        iils = nint(xils)
        rest = xils - real(iils,8)
        ilswert = jobils(iils) + 0.5 * rest * (jobils(iils+1) - jobils(iils-1) &
          + rest * (jobils(iils+1) - 2.0 * jobils(iils) + jobils(iils-1)))
        sumwert = sumwert + ilswert * wrkisa(j) * (wvskal%nue_isa(j+1) - wvskal%nue_isa(j-1))
        sumils = sumils + ilswert * (wvskal%nue_isa(j+1) - wvskal%nue_isa(j-1))
    end do
    specxils(i) = sumwert / sumils
end do

! calculate derivative wrt nue (use quintic poly interpolation)
dspecxilsdnue(1) = specxils(2) - specxils(1)
dspecxilsdnue(2) = 0.5 * (specxils(3) - specxils(1))
do i = 3,job(ijob)%ngrid_mess - 2
    dspecxilsdnue(i) = 8.333333e-2 * (specxils(i-2) - 8.0 * specxils(i-1) &
      + 8.0 * specxils(i+1) - specxils(i+2))
end do
dspecxilsdnue(job(ijob)%ngrid_mess-1) = &
  0.5 * (specxils(job(ijob)%ngrid_mess) - specxils(job(ijob)%ngrid_mess-2))
dspecxilsdnue(job(ijob)%ngrid_mess) &
  = specxils(job(ijob)%ngrid_mess) - specxils(job(ijob)%ngrid_mess-1)

! renormalize shift to scale derivative
kwmidnue = 2.0 / real(job(ijob)%nuel_mess + job(ijob)%nuer_mess)
do i =1,job(ijob)%ngrid_mess
    nue = real(job(ijob)%nuel_mess + wvskal%dnue_mess * real(i - 1,8))
    dspecxilsdnue(i) = - dspecxilsdnue(i) * nue * kwmidnue
end do

end subroutine make_spec



!====================================================================
!  make_tau
!====================================================================
subroutine make_tau(ispec,ijob,polytau,wrktau)

use globinv10

implicit none

integer,intent(in) :: ispec,ijob
real,dimension(wvskal%ngrid_ref,maxpoly,n_tau),intent(in) :: polytau
real,dimension(wvskal%ngrid_ref,n_tau),intent(inout) :: wrktau

integer :: i,j,k
real(8) :: airmass,wert
real(8),dimension(maxpoly) :: coeff

airmass = 1 / cos(obs(ispec)%sza_rad)
do i = 1,maxpoly
    coeff(i) = airmass ** (2 * (i - 1))
end do

do i = 1,n_tau
    if (job(ijob)%method(i) .gt. 0) then
        do j = job(ijob)%igridl_ref,job(ijob)%igridr_ref
            wert = 0.0d0
            do k = 1,maxpoly
                wert = wert + coeff(k) * polytau(j,k,i)
            end do
            wrktau(j,i) = airmass * wert
        end do
    end if
end do

end subroutine make_tau



!====================================================================
!  make_tau_extd
!====================================================================
subroutine make_tau_extd(ispec,ijob,polytau,dtau_dp,dtau_dT,dp,dT,wrktau)

use globinv10

implicit none

integer,intent(in) :: ispec,ijob
real,dimension(wvskal%ngrid_ref,maxpoly,n_tau),intent(in) :: polytau
real,dimension(wvskal%ngrid_ref,n_tau),intent(in) :: dtau_dp,dtau_dT
real,intent(in) :: dp,dT
real,dimension(wvskal%ngrid_ref,n_tau),intent(inout) :: wrktau

integer :: i,j,k
real(8) :: airmass,wert
real(8),dimension(maxpoly) :: coeff

airmass = 1 / cos(obs(ispec)%sza_rad)
do i = 1,maxpoly
    coeff(i) = airmass ** (2 * (i - 1))
end do

do i = 1,n_tau
    if (job(ijob)%method(i) .gt. 0) then
        do j = job(ijob)%igridl_ref,job(ijob)%igridr_ref
            wert = 0.0d0
            do k = 1,maxpoly
                wert = wert + coeff(k) * polytau(j,k,i)
            end do
            wrktau(j,i) = airmass * (wert + dp * dtau_dp(j,i) + dT * dtau_dT(j,i))
        end do
    end if
end do

end subroutine make_tau_extd



!====================================================================
!  make_trans
!====================================================================
subroutine make_trans(ijob,wrktau,solspec,wrktrm)

use globinv10

implicit none

integer,intent(in) :: ijob
real,dimension(wvskal%ngrid_ref,n_tau),intent(in) :: wrktau
real,dimension(wvskal%ngrid_ref),intent(in) :: solspec
real,dimension(wvskal%ngrid_ref),intent(inout) :: wrktrm

integer :: i,j

wrktrm(job(ijob)%igridl_ref:job(ijob)%igridr_ref) = 0.0
do i = 1,n_tau
    if (job(ijob)%method(i) .gt. 0) then
        do j = job(ijob)%igridl_ref,job(ijob)%igridr_ref
            wrktrm(j) = wrktrm(j) + job(ijob)%colskal(i) * wrktau(j,i)
        end do
    end if
end do

do i = job(ijob)%igridl_ref,job(ijob)%igridr_ref
    wrktrm(i) = myexp(-wrktrm(i)) * solspec(i)
end do

contains

real function myexp(xwert)

implicit none

real,intent(in) :: xwert

real :: x

if (xwert .gt. 0.0) then
    myexp = 1.0 + xwert
else
    if (xwert .gt. - 1.0) then ! approximation better than 5e-5 relative deviation
        x = abs(xwert)
        myexp = 1.0 / &
          (1.0 + x * (1.0 + x * (0.5039 + x * (0.1491 + x * 0.0653))))
    else
        if (xwert .gt. - 15.0) then
            myexp = exp(xwert)
        else
            myexp = 3.059e-7
        end if
    end if
end if

end function myexp

end subroutine make_trans



!====================================================================
!  matinvers: invertiert eine symmetrische nmax x nmax Matrix
!====================================================================
subroutine matinvers(nmax,LMstab,matein,mataus,inverfolg)

implicit none

integer,intent(in) :: nmax
real,intent(in) :: LMstab
real,dimension(nmax,nmax),intent(in) :: matein
real,dimension(nmax,nmax),intent(out) :: mataus
logical,intent(out) :: inverfolg

logical :: warnung
logical,dimension(nmax):: done
integer :: i,j,k,l,jj,kk,jk,lk,nrank,nvmax,icount
real,dimension(:,:),allocatable :: matein_stab,mat_wrk
real(8) :: check
real(8) :: vkk,vjk,pivot
real(8),dimension(:),allocatable :: v

! add LM values to matein
allocate (matein_stab(nmax,nmax),mat_wrk(nmax,nmax))
matein_stab = matein
do i = 1,nmax
    matein_stab(i,i) = matein_stab(i,i) + LMstab
end do

! Eindimensionale Darstellung der symmetrischen Eingabematrix in v
nvmax = (nmax * nmax + nmax) / 2
allocate (v(nvmax))

! Werte in v eintragen und diag eintragen
icount = 0
do i = 1,nmax ! Zeilenindex
    do j = 1,i ! Spaltenindex
        icount = icount + 1
        v(icount) = matein_stab(j,i)
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
mat_wrk = matmul(mataus,matein_stab)
do i = 1,nmax
    mat_wrk(i,i) = mat_wrk(i,i) - 1.0
end do

do i = 1,nmax
    do j = 1,nmax
        if (abs(mat_wrk(j,i)) .gt. 1.0d-4) warnung = .true.
    end do
end do

deallocate (matein_stab,mat_wrk)

if (warnung) then
    print *,'subroutine matinvers: inverted matrix incorrect!'
    inverfolg = .false.
else
    inverfolg = .true.
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
!  postprocessing
!====================================================================
subroutine postprocessing(dp,totcol_ref,ispec)

use globinv10

implicit none

real,intent(in) :: dp
real(8),dimension(n_tau),intent(in) :: totcol_ref
integer,intent(in) :: ispec

integer :: i,j
real(8) :: sin2phi,g_earth,col_corr_air,col_corr_h2o

col_corr_h2o = 0.0
col_corr_air = -1.0

do i  =  1,n_job
    do j = 1,n_tau
        if (job(i)%method(j) .eq. 2) then
            postpro(i)%col_corr(j) = job(i)%colskal(j) * totcol_ref(j) * postpro(i)%AICF(j) &
              * sza_corr(obs(ispec)%sza_rad,postpro(i)%ADCF1(j),postpro(i)%ADCF2(j))
            
            if (postpro(i)%Xident(j) .eq. "XH2O    ") then
                col_corr_h2o = postpro(i)%col_corr(j)
            else
                if (postpro(i)%Xident(j) .eq. "XAIR    ") then
                    col_corr_air = 4.77395 * postpro(i)%col_corr(j) !assume O2 molar fraction of 0.20947
                end if
            end if
        end if
    end do
end do

do i = 1,n_job
    do j = 1,n_tau
        if (job(i)%method(j) .eq. 2) then
            if (postpro(i)%Xident(j) .eq. "XAIR    ") then
                sin2phi = sin(obs(ispec)%latrad) * sin(obs(ispec)%latrad)
                g_earth = 9.780325d0 * ((1.0d0 + 1.931853d-3 * sin2phi) &
                  / sqrt(1.0d0 - 6.694380d-3 * sin2phi)) - 3.086d-6 * altim_gnd_ref
                postpro(i)%XVMR(j) = (28.97d0 * col_corr_air + 18.02d0 * col_corr_h2o) &
                  * amu_SI * g_earth / (pPa_gnd_ref + dp)
            else
                postpro(i)%XVMR(j) = 1.0e6 * postpro(i)%col_corr(j) / col_corr_air
            end if
        end if
    end do
end do

contains

real function sza_corr(sza_rad,ADCF1,ADCF2)

implicit none

real(8),intent(in) :: sza_rad
real,intent(in) :: ADCF1,ADCF2

real :: x,xref,xquad,xrefquad

x = 0.63661977 * sza_rad
xref = 0.66666666
xquad = x * x * x * x
xrefquad = xref * xref * xref * xref

sza_corr = (1.0 + xquad * (ADCF1 + xquad * xquad * ADCF2)) &
  / ((1.0 + xrefquad * (ADCF1 + xrefquad * xrefquad * ADCF2)))

end function sza_corr

end subroutine postprocessing



!====================================================================
! read_invinput: read general input 
!====================================================================
subroutine read_invinput(pfadname,filename)

use globinv10

implicit none

character(len=*),intent(in) :: pfadname,filename

character(len=300) :: infile
character(len=12) :: zeile
logical :: marke,dateidadec
integer :: iunit_inv,iunit_ils,next_free_unit,iowert,i,j
complex(8) :: mwbds

infile = pfadname // pathstr // filename

iunit_inv = next_free_unit()
open (iunit_inv,file = infile,iostat = iowert,status = 'old',action = 'read')

if (iowert .ne. 0) then
    print *,'Cannot read input file:    '
    print *,infile
end if

call gonext(iunit_inv,.false.)
read (iunit_inv,'(A)') datumspfad
read (iunit_inv,'(A)') sitename
read (iunit_inv,'(A)') yymmddchar
read (iunit_inv,'(A)') abscodatei
read (iunit_inv,*) pTdetaildec
print *,'date folder:               ',datumspfad
print *,'site name:                 ',sitename
print *,'yymmdd:                    ',yymmddchar
print *,'abscodatei:                ',abscodatei
print *,'pTdetaildec:               ',pTdetaildec

! check consistency of datumspfad, abscodatei and yymmddcar
if (index(datumspfad,yymmddchar) .eq. 0) then
    print *,datumspfad
    print *,yymmddchar
    call warnout('inconsistent date folder!',1)
end if
if (index(abscodatei,yymmddchar) .eq. 0) then
    print *,abscodatei
    print *,yymmddchar
    call warnout('inconsistent absco file!',1)
end if

call gonext(iunit_inv,.false.)
read (iunit_inv,*) refractdec

instr%OPDmax = 1.8d0
! check for optional input file (ILS parameters superimposed to ILS parameters in bin-file)
inquire (file = pfadname//pathstr//'ils_corr.inp',exist = dateidadec)
if (dateidadec) then
    iunit_ils = next_free_unit()
    open (iunit_ils,file = pfadname //pathstr//'ils_corr.inp',status = 'old',action = 'read')
    call gonext(iunit_ils,.false.)
    read (iunit_ils,*) instr%apolin_inp,instr%apophas_inp,instr%apoeff_inp
    close (iunit_ils)
else
    instr%apolin_inp = 1.0d0
    instr%apoeff_inp = 0.0d0
    instr%apophas_inp = 0.0d0
end if

print *,'OPDmax:       ',instr%OPDmax
print *,'apolin_inp:   ',instr%apolin_inp
print *,'apoeff_inp:   ',instr%apoeff_inp
print *,'phaserr_inp:  ',instr%apophas_inp

call gonext(iunit_inv,.false.)
read (iunit_inv,*) n_job
read (iunit_inv,*) n_tau
read (iunit_inv,*) persist
print *,'number of jobs:            ',n_job
print *,'number of species:         ',n_tau
print *,'persistence:       ',persist

if (n_job .gt. maxjob) then
    print *,'max number of jobs:        ',maxjob
    call warnout('Too many jobs!',0)
end if
if (n_tau .gt. maxtau) then
    print *,'max number of jobs:        ',maxtau
    call warnout('Too many species!',0)
end if

if (persist .lt. 0.0 .or. persist .gt. 1.0) then
    persist = 0.5
    call warnout('persist set to 0.5!',1)
end if

call gonext(iunit_inv,.false.)
do i = 1,n_job
    print *,'Job in process...',i
    read (iunit_inv,*) mwbds
    job(i)%nuel_input = real(mwbds,8)
    job(i)%nuer_input = aimag(mwbds)
    print *,'requested microwindow bounds:',mwbds
    job(i)%ngas = 0
    job(i)%nderigas = 0
    do j = 1,n_tau
        read(iunit_inv,*) job(i)%method(j)
        print *,'method: ',job(i)%method(j)
        if (job(i)%method(j) .gt. 0) job(i)%ngas = job(i)%ngas + 1
        if (job(i)%method(j) .gt. 1) then
            job(i)%nderigas = job(i)%nderigas + 1
            read(iunit_inv,*) postpro(i)%AICF(j), &
              postpro(i)%ADCF1(j),postpro(i)%ADCF2(j),postpro(i)%Xident(j)
        end if
    end do
    print *,'gases in forward calc:         ',job(i)%ngas
    print *,'derived gases in forward calc: ',job(i)%nderigas
    read(iunit_inv,*) job(i)%nbase
    if (job(i)%nbase .gt. maxbase) then
        print *,'job  ndww  maxdww',i,job(i)%nbase,maxbase
        call warnout('Too many baseline pts! ',0)
    end if
    if (job(i)%nbase .lt. 1) then
        print *,'job: ',i
        call warnout('Nof baseline pts < 1! ',0)
    end if
    read(iunit_inv,*) job(i)%ndww
    if (job(i)%ndww .gt. maxdww) then
        print *,'job  ndww  maxdww',i,job(i)%ndww,maxdww
        call warnout('Too many dww windows! ',0)
    end if
    do j = 1,job(i)%ndww
        read(iunit_inv,*) job(i)%vw_bnds(j),job(i)%vw_steep(j)
        print *,'deweighting: ',job(i)%vw_bnds(j),job(i)%vw_steep(j)
    end do
end do

! determine number of raw measurements to treat
call gonext(iunit_inv,.false.)
marke = .false.
n_spectra = 0
do while (.not. marke)
    read(iunit_inv,'(A)') zeile    
    if (zeile(1:3) .eq. '***') then
        marke = .true.
    else
        n_spectra = n_spectra + 1
        if (n_spectra .gt. maxspectra) then
            print*,'n_spectra:  ',n_spectra
            print*,'maxspectra: ',maxspectra
            call warnout('Too many spectra!',0)
        else
            specname(n_spectra) = zeile
        end if
    end if
end do
close (iunit_inv)

print *,'number of spectra: ',n_spectra

end subroutine read_invinput



!====================================================================
!  read_messpec
!====================================================================
subroutine read_messpec(filename,ngrid,messpec)

implicit none

character(len=*) :: filename
integer,intent(in) :: ngrid
real,dimension(ngrid),intent(inout) :: messpec

character(len=2) :: dumchar
integer :: iunit_inv,next_free_unit,i,iowert,dumint
real(8) :: dumdble

iunit_inv = next_free_unit()
open (iunit_inv,file = filename,iostat = iowert,access ='stream',status = 'old',action = 'read')

if (iowert .ne. 0) then
    print *,filename
    call warnout ('Cannot open measured spectrum!',0)
end if

do i = 1,6
    call gonext(iunit_inv,.true.)
end do
read(iunit_inv) dumchar
read(iunit_inv) dumdble
read(iunit_inv) dumdble
read(iunit_inv) dumint

read(iunit_inv) messpec(1:ngrid)

close (iunit_inv)

end subroutine read_messpec



!====================================================================
!  read_pTintraday
!====================================================================
subroutine read_pTintraday(datumspfad,ndpTdt,HHMMSSdpTdt,dpdt,dTdt)

use globinv10, only : pathstr,pPa_gnd_ref

implicit none

integer,intent(in) :: ndpTdt

character(len=*),intent(in) :: datumspfad
character(len=6),dimension(ndpTdt),intent(out) :: HHMMSSdpTdt
real,dimension(ndpTdt),intent(out) :: dpdt,dTdt

integer :: iunit_inv,next_free_unit,iowert,i
real :: phPa

iunit_inv = next_free_unit()
open (iunit_inv,file = trim(datumspfad)//pathstr//'pT'//pathstr//'pT_intraday.inp' &
  ,status = 'old',iostat = iowert,action = 'read')

if (iowert .ne. 0) then
    call warnout ('Cannot open pT_intraday.dat file!',0)
end if

call gonext(iunit_inv,.false.)
do i = 1,ndpTdt
    read (iunit_inv,*) HHMMSSdpTdt(i),phPa,dTdt(i)
    dpdt(i) = phPa - 0.01d0 * pPa_gnd_ref
end do

close (iunit_inv)

end subroutine read_pTintraday


!====================================================================
!  read_stored_arrays: reads arrays
!====================================================================
subroutine read_stored_arrays(filename,solspec_ref,totcol_ref &
  ,polytau,dtau_dp,dtau_dT)

use globinv10

implicit none

real,dimension(wvskal%ngrid_ref),intent(out) :: solspec_ref
real(8),dimension(n_tau),intent(out) :: totcol_ref
real,dimension(wvskal%ngrid_ref,maxpoly,n_tau),intent(out) :: polytau
real,dimension(wvskal%ngrid_ref,n_tau),intent(out) :: dtau_dp,dtau_dT

character(len=*),intent(in) :: filename

integer :: iunit_inv,next_free_unit,iowert,dumint,i,j
real(8) :: dumdble

iunit_inv = next_free_unit()
open (iunit_inv,file = filename,access ='stream' &
  ,status = 'old',iostat = iowert,action = 'read')

if (iowert .ne. 0) then
    call warnout ('Cannot access stored abscos!',0)
end if

! all integers for array allocations
read (iunit_inv) dumint !n_Tdisturb
read (iunit_inv) dumint !maxpoly
read (iunit_inv) dumint !wvskal%ngrid_ref
read (iunit_inv) dumint !n_tau

! all floats for further aux infos
read (iunit_inv) dumdble !altim_gnd_ref
read (iunit_inv) dumdble !pPa_gnd_ref
read (iunit_inv) dumdble !TKel_gnd_ref
read (iunit_inv) dumdble !wvskal%firstnue
read (iunit_inv) dumdble !wvskal%dnuerel

! total column of each species (real8)
do i = 1,n_tau
    read (iunit_inv) totcol_ref(i)
end do

! solar spectrum (real)
read (iunit_inv) solspec_ref(1:wvskal%ngrid_ref)

! for each species: polytau (real),polytau_dp (real),polytau_dT (real)
do i = 1,n_tau
    do j = 1,maxpoly
        read (iunit_inv) polytau(1:wvskal%ngrid_ref,j,i)
    end do
    read (iunit_inv) dtau_dp(1:wvskal%ngrid_ref,i)
    read (iunit_inv) dtau_dT(1:wvskal%ngrid_ref,i)
end do

close (iunit_inv)

end subroutine read_stored_arrays



!====================================================================
!  refraction
!====================================================================
real(8) function refraction_rad(sza_rad,pPa_gnd,TKel_gnd)

use globinv10, only : radtograd,gradtorad,pi

implicit none

real(8),intent(in) :: sza_rad,pPa_gnd,TKel_gnd

real(8) :: hoehe,wert

hoehe = radtograd * (0.5d0 * pi - sza_rad)
wert = 8.179d-7 / tan(gradtorad * (hoehe + (10.3d0 / (hoehe + 5.11d0))))
refraction_rad = wert * pPa_gnd / TKel_gnd

end function refraction_rad



!====================================================================
!  specnormcut
!====================================================================
subroutine specnormcut(ijob,sollnorm,fullmess,messxils)

use globinv10

implicit none

integer,intent(in) :: ijob
real,intent(in) :: sollnorm
real,dimension(wvskal%ngrid_mess),intent(in) :: fullmess
real,dimension(job(ijob)%ngrid_mess),intent(out) :: messxils

integer :: i,j,ix,isinc,ils_mess
real :: xwert,xr,ilswert
real(8) :: norm,sumwert,sumils,deltanue,kwdnue

! determine normalization factor
sumwert = 0.0
do i = job(ijob)%igridl_mess,job(ijob)%igridr_mess
    sumwert = sumwert + fullmess(i)
end do
norm = sumwert / real(job(ijob)%ngrid_mess)
norm = sollnorm / norm

do i = job(ijob)%igridl_mess,job(ijob)%igridr_mess
    messxils(i-job(ijob)%igridl_mess+1) = norm * fullmess(i)
end do

end subroutine specnormcut



!====================================================================
!  sol_ephem: determine radial velocity of the sun
!====================================================================
subroutine sol_ephem(obs_lat,obs_lon,JDdate,solskal)

implicit none

real(8),intent(in) :: obs_lat,obs_lon,JDdate
real(8),intent(out) :: solskal

real(8),parameter :: JDref_orb = 2451547.507d0  ! reference perihel (Nach Meeus. S. 272)
real(8),parameter :: JDref_equ = 2451623.816d0  ! reference equinox Mar 20, 2000, 7h35m UT
real(8),parameter :: omega_ano = 1.7202122d-2   ! anomalistic year 365.2597 d (Nach Meeus. S. 272)
real(8),parameter :: gradtorad = 1.745329252d-2
real(8),parameter :: exzen = 0.0167d0           ! excentricity of earth orbit


integer :: k
real(8) :: delta_d,exzano,dtexzano,trueano,trueano_equ &
  ,solskal_orb,solskal_moon,solskal_day,sun_dec,dteq,taux,JDmoon,nwert,lamwert,gwert,lwert

! annual orbital motion
! distance to sun is r = a * (1 - e**2) / (1 + e * cos(true_anomaly))
! approx for true_anomaly = om * t + e * sin(om * t) + 5/16 * e**2 * sin(2 * om * t)
delta_d = JDdate - JDref_orb
exzano = omega_ano * delta_d + exzen * sin(omega_ano * delta_d)
dtexzano = omega_ano * (1.0d0 + exzen * cos(omega_ano * delta_d))
solskal_orb = - 5.77552d-3 * exzen * sin(exzano) * dtexzano ! prefactor is AE[m]  / clight[m/s] * LOD[s]

! lunar contribution
! find date of new moon nearest to selected date
! pre-estimate nearest date
k = int(0.033863192 * (JDdate - 2451550.09765d0))
! calculate accurate JD of new moon (Meeus S. 348)
taux = 8.0850548d-4 * real(k,8)
JDmoon = 2451550.09765d0 + 29.530588853 * real(k,8) &
+ taux * taux * (0.0001337 + taux * (-1.5d-7 + 7.3e-10 * taux))
solskal_moon = 3.85d-8 * sin(0.212989d0 * (JDdate - JDmoon))

! diurnal motion
! estimate declination of sun (neglecting precession)
delta_d = JDdate - JDref_orb
trueano = omega_ano * delta_d + exzen * sin(omega_ano * delta_d)
delta_d = JDref_equ - JDref_orb
trueano_equ = omega_ano * delta_d + exzen * sin(omega_ano * delta_d)
sun_dec = 0.41015d0 * sin(trueano - trueano_equ)
! estimate equation of time (true time - mean time) in rad
nwert = JDdate - 2451545.0d0
lwert = gradtorad * (280.46d0 + 0.9856474d0 * nwert)
gwert = gradtorad * (357.528d0 + 0.9856003d0 * nwert)
lamwert = lwert + 1.915d0 * gradtorad * sin(gwert) + 0.020d0 * gradtorad * sin(2.0d0 * gwert)
dteq = 4.3633d-3 * (9.863d0 * sin(2.0d0 * lamwert) - 0.212d0 * sin(4.0d0 * lamwert) &
  - 7.66d0 * sin(gwert) - 0.08d0 * sin(2.0d0 * gwert))
! prefactor in eq below is 2 * pi * rearth[m] / (clicht[m/s] * LOD [s])
solskal_day = - 1.5454d-6 * cos(obs_lat) * cos(sun_dec) &
  * sin(6.2831853072d0 * (JDdate - int(JDdate)) + obs_lon + dteq)

solskal = solskal_orb + solskal_moon + solskal_day

end subroutine sol_ephem



!====================================================================
!  tofile_ils: write ILS array to file
!====================================================================
subroutine tofile_ils(filename,dnue_ils,n_ils,ils_radius,ils)

use globinv10, only : pathstr

implicit none

character(len=*),intent(in) :: filename
real(8),intent(in) :: dnue_ils
integer,intent(in) :: n_ils,ils_radius
real,dimension(-ils_radius:ils_radius,n_ils),intent(in) :: ils

integer :: i,j,iunit_inv,next_free_unit

iunit_inv = next_free_unit()
open (iunit_inv,file = 'wrk_fast'//pathstr//filename,status = 'replace')
do i = -ils_radius,ils_radius
    write (iunit_inv,'(ES15.8,20(1X,ES12.4))') &
      dnue_ils * real(i,8),(ils(i,j),j = 1,n_ils)
end do
close (iunit_inv)

end subroutine tofile_ils



!====================================================================
!  write tau_lev for each species to file
!====================================================================
subroutine tofile_jak(filename,ijob,npts,nderi,jak)

use globinv10, only : pathstr

implicit none

character(len=*),intent(in) :: filename
integer,intent(in) :: ijob,npts,nderi
real,dimension(npts,nderi),intent(in) :: jak

character(2) :: exta
integer :: iunit_inv,next_free_unit,iowert,j,k

write (exta,'(I2.2)') ijob
iunit_inv = next_free_unit()
open (iunit_inv,file = 'wrk_fast'//pathstr//filename//exta//'.dat'&
  ,status = 'replace',iostat = iowert)
if (iowert .ne. 0) then
    call warnout ('tofile_jak: cannot open file!',0)
end if
do j = 1,npts
    write (iunit_inv,'(500(1X,ES12.4))') (jak(j,k),k=1,nderi)
end do
close (iunit_inv)

end subroutine tofile_jak



!====================================================================
!  tofile_solspec
!====================================================================
subroutine tofile_solspec(filename,ngrid,nue,solspec_ref,solspec)

use globinv10, only : pathstr

implicit none

character(len=*),intent(in) :: filename
integer,intent(in) :: ngrid
real(8),dimension(ngrid),intent(in) :: nue
real,dimension(ngrid),intent(in) :: solspec_ref,solspec

integer :: iunit_inv,next_free_unit,i

iunit_inv = next_free_unit()
open (iunit_inv,file = 'wrk_fast'//pathstr//filename//'.dat',status = 'replace')
do i = 1,ngrid
    write (iunit_inv,'(F14.7,1X,F8.4,1X,F8.4)') nue(i),solspec_ref(i),solspec(i)
end do
close (iunit_inv)

end subroutine tofile_solspec



!====================================================================
!  tofile_specxils
!====================================================================
subroutine tofile_specxils(filename,ijob,ngrid,firstnue,dnue,specxils)

use globinv10, only : pathstr

implicit none

character(len=*),intent(in) :: filename
integer,intent(in) :: ijob,ngrid
real(8),intent(in) :: firstnue,dnue
real,dimension(ngrid),intent(in) :: specxils

character(2) :: exta
integer :: iunit_inv,next_free_unit,i
real(8) :: nue

write (exta,'(I2.2)') ijob
iunit_inv = next_free_unit()
open (iunit_inv,file = 'wrk_fast'//pathstr//filename//exta//'.dat',status = 'replace')
do i = 1,ngrid
    nue = firstnue + dnue * real(i-1,8)
    write (iunit_inv,'(F14.7,1X,F8.4)') nue,specxils(i)
end do
close (iunit_inv)


end subroutine tofile_specxils



!====================================================================
!  tofile_trm
!====================================================================
subroutine tofile_trm(filename,ijob,ngrid,igridl,igridr,nue,trm)

use globinv10, only : pathstr

implicit none

character(len=*),intent(in) :: filename
integer,intent(in) :: ijob,ngrid,igridl,igridr
real(8),dimension(ngrid),intent(in) :: nue
real,dimension(ngrid),intent(in) :: trm

character(2) :: exta
integer :: iunit_inv,next_free_unit,iowert,i

write (exta,'(I2.2)') ijob
iunit_inv = next_free_unit()
open (iunit_inv,file = 'wrk_fast'//pathstr//filename//exta//'.dat'&
  ,status = 'replace',iostat = iowert)
if (iowert .ne. 0) then
    call warnout ('tofile_trm: cannot open file!',0)
end if
do i = igridl,igridr
    write (iunit_inv,'(F14.7,1X,F8.4)') nue(i),trm(i)
end do
close (iunit_inv)

end subroutine tofile_trm



!====================================================================
!  Warnung rausschreiben und Programm evtl. beenden
!====================================================================
subroutine warnout(text,predec)

implicit none

character(len=*),intent(in) :: text
integer,intent(in) :: predec
integer :: intdec

print *,'Warning:'
print *, trim(text)
if (predec .eq. 0) then
    print *,'This is a critical error, press return for terminating exection.'
    read *,intdec
    stop
else
    print *,'Shutdown program: enter 0 / proceed with exection: enter 1:'
    read *, intdec
    if (intdec .eq. 0) stop
end if

end subroutine warnout

