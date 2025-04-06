package com.example.databaseimport.mapper;

import com.example.databaseimport.entity.Student;
import org.apache.ibatis.annotations.*;
import java.util.List;

@Mapper
public interface StudentMapper {
    
    @Update({
        "CREATE TABLE IF NOT EXISTS student (",
        "  registno VARCHAR(20) NOT NULL,",
        "  name VARCHAR(50),",
        "  kdno VARCHAR(10) NOT NULL,",
        "  kcno INT NOT NULL,",
        "  ccno INT NOT NULL,",
        "  seat INT,",
        "  PRIMARY KEY (registno),",
        "  FOREIGN KEY (kdno, kcno, ccno) REFERENCES room(kdno, kcno, ccno)",
        ")"
    })
    void createTable();
    
    @Insert({
        "INSERT INTO student(registno, name, kdno, kcno, ccno, seat)",
        "VALUES(#{registno}, #{name}, #{kdno}, #{kcno}, #{ccno}, #{seat})"
    })
    void insert(Student student);
    
    @Insert({
        "<script>",
        "INSERT INTO student(registno, name, kdno, kcno, ccno, seat) VALUES",
        "<foreach collection='list' item='item' separator=','>",
        "(#{item.registno}, #{item.name}, #{item.kdno}, #{item.kcno}, #{item.ccno}, #{item.seat})",
        "</foreach>",
        "</script>"
    })
    void batchInsert(@Param("list") List<Student> students);
    
    @Select("SELECT COUNT(*) FROM student")
    int count();
    
    @Select("SELECT * FROM student LIMIT 10")
    List<Student> selectSample();
} 