package com.example.databaseimport.mapper;

import com.example.databaseimport.entity.Room;
import org.apache.ibatis.annotations.*;
import java.util.List;

@Mapper
public interface RoomMapper {
    
    @Update({
        "CREATE TABLE IF NOT EXISTS room (",
        "  kdno VARCHAR(10) NOT NULL,",
        "  kcno INT NOT NULL,",
        "  ccno INT NOT NULL,",
        "  kdname VARCHAR(50),",
        "  exptime DATETIME,",
        "  papername VARCHAR(50),",
        "  PRIMARY KEY (kdno, kcno, ccno)",
        ")"
    })
    void createTable();
    
    @Insert({
        "INSERT INTO room(kdno, kcno, ccno, kdname, exptime, papername)",
        "VALUES(#{kdno}, #{kcno}, #{ccno}, #{kdname}, #{exptime}, #{papername})"
    })
    void insert(Room room);
    
    @Insert({
        "<script>",
        "INSERT INTO room(kdno, kcno, ccno, kdname, exptime, papername) VALUES",
        "<foreach collection='list' item='item' separator=','>",
        "(#{item.kdno}, #{item.kcno}, #{item.ccno}, #{item.kdname}, #{item.exptime}, #{item.papername})",
        "</foreach>",
        "</script>"
    })
    void batchInsert(@Param("list") List<Room> rooms);
    
    @Select("SELECT COUNT(*) FROM room")
    int count();
    
    @Select("SELECT * FROM room LIMIT 10")
    List<Room> selectSample();
} 