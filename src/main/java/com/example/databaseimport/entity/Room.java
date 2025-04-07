package com.example.databaseimport.entity;

import java.util.Date;
import java.util.Objects;

public class Room {
    private String kdno;    // 考点号
    private Integer kcno;   // 考场号
    private Integer ccno;   // 场次号
    private String kdname;  // 考点名称
    private Date exptime;   // 预计开考时间
    private String papername; // 指定试卷号

    public Room() {
    }

    public Room(String kdno, Integer kcno, Integer ccno, String kdname, Date exptime, String papername) {
        this.kdno = kdno;
        this.kcno = kcno;
        this.ccno = ccno;
        this.kdname = kdname;
        this.exptime = exptime;
        this.papername = papername;
    }

    public String getKdno() {
        return kdno;
    }

    public void setKdno(String kdno) {
        this.kdno = kdno;
    }

    public Integer getKcno() {
        return kcno;
    }

    public void setKcno(Integer kcno) {
        this.kcno = kcno;
    }

    public Integer getCcno() {
        return ccno;
    }

    public void setCcno(Integer ccno) {
        this.ccno = ccno;
    }

    public String getKdname() {
        return kdname;
    }

    public void setKdname(String kdname) {
        this.kdname = kdname;
    }

    public Date getExptime() {
        return exptime;
    }

    public void setExptime(Date exptime) {
        this.exptime = exptime;
    }

    public String getPapername() {
        return papername;
    }

    public void setPapername(String papername) {
        this.papername = papername;
    }

    @Override
    public String toString() {
        return "Room{" +
                "kdno='" + kdno + '\'' +
                ", kcno=" + kcno +
                ", ccno=" + ccno +
                ", kdname='" + kdname + '\'' +
                ", exptime=" + exptime +
                ", papername='" + papername + '\'' +
                '}';
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Room room = (Room) o;
        return Objects.equals(kdno, room.kdno) &&
                Objects.equals(kcno, room.kcno) &&
                Objects.equals(ccno, room.ccno) &&
                Objects.equals(kdname, room.kdname) &&
                Objects.equals(exptime, room.exptime) &&
                Objects.equals(papername, room.papername);
    }

    @Override
    public int hashCode() {
        return Objects.hash(kdno, kcno, ccno, kdname, exptime, papername);
    }
} 